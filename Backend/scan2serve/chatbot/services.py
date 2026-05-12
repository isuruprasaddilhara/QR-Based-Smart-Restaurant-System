# services.py

import json
from collections import defaultdict
from decimal import Decimal
from typing import Optional, List

from django.conf import settings
from django.db.models import (
    Avg,
    Count,
    Sum,
    Q,
)

from openai import OpenAI

from menu.models import MenuItem, MenuCategory
from orders.models import OrderItem
from favourites.models import FavoriteMenuItem

client = OpenAI(api_key=settings.OPENAI_API_KEY)

# =========================================================
# MEMORY STORAGE
# =========================================================

CONVERSATION_MEMORY = defaultdict(list)

MAX_HISTORY = 30


# =========================================================
# HELPERS
# =========================================================

def money(value):

    if value is None:
        return "0.00"

    if isinstance(value, Decimal):
        return f"{value:.2f}"

    return str(value)


def normalize(text: str):

    return (text or "").strip().lower()


# =========================================================
# CONVERSATION MEMORY
# =========================================================

def get_conversation_key(user, session_id=None):

    if user and user.is_authenticated:
        return f"user_{user.id}"

    if session_id:
        return f"guest_{session_id}"

    return "anonymous"


def save_message(conversation_key, message):

    CONVERSATION_MEMORY[conversation_key].append(message)

    CONVERSATION_MEMORY[conversation_key] = (
        CONVERSATION_MEMORY[conversation_key][-MAX_HISTORY:]
    )


def get_conversation_history(conversation_key):

    return CONVERSATION_MEMORY.get(conversation_key, [])


def clear_conversation(conversation_key):

    CONVERSATION_MEMORY[conversation_key] = []


# =========================================================
# CONTEXT EXTRACTION  (FIXED)
# =========================================================

def extract_context_from_history(history):

    context = {
        "last_dish": None,
        "last_category": None,
        "last_intent": None,
        "last_recommended_dishes": [],   # NEW: track all recently mentioned dishes
    }

    # Only look at recent messages
    recent_messages = history[-10:]

    # Pre-load all menu items and categories once (no arbitrary limit)
    all_items = list(MenuItem.objects.select_related("category").all())
    all_categories = list(MenuCategory.objects.all())

    # Reverse search → newest first so we get the MOST RECENT context
    for msg in reversed(recent_messages):

        role = msg.get("role", "")
        content = (
            str(msg.get("content", ""))
            .lower()
            .strip()
        )

        if not content:
            continue

        # =================================================
        # FIND LAST MENU ITEM
        # Fix: previously used name__icontains=content (backwards).
        # Now correctly checks: item.name.lower() in content
        # Prioritise assistant messages since that's where
        # recommendations are stated.
        # =================================================

        if not context["last_dish"]:

            for item in all_items:
                if item.name.lower() in content:
                    context["last_dish"] = item.name
                    break

        # Collect ALL dishes mentioned in assistant messages
        # so we can refer back to any of them
        if role == "assistant" and not context["last_recommended_dishes"]:

            mentioned = [
                item.name
                for item in all_items
                if item.name.lower() in content
            ]

            if mentioned:
                context["last_recommended_dishes"] = mentioned

        # =================================================
        # FIND LAST CATEGORY
        # =================================================

        if not context["last_category"]:

            for category in all_categories:

                if category.name.lower() in content:
                    context["last_category"] = category.name
                    break

        # =================================================
        # FIND LAST INTENT
        # =================================================

        if not context["last_intent"]:

            if any(
                word in content
                for word in [
                    "recommend",
                    "suggest",
                    "popular",
                    "best",
                ]
            ):
                context["last_intent"] = "recommendation"

            elif any(
                word in content
                for word in [
                    "price",
                    "cost",
                    "expensive",
                    "cheap",
                ]
            ):
                context["last_intent"] = "pricing"

            elif any(
                word in content
                for word in [
                    "ingredient",
                    "contains",
                    "made of",
                ]
            ):
                context["last_intent"] = "ingredients"

            elif any(
                word in content
                for word in [
                    "detail",
                    "more",
                    "describe",
                ]
            ):
                context["last_intent"] = "details"

        # Stop early once we have everything we need
        if (
            context["last_dish"]
            and context["last_category"]
            and context["last_intent"]
            and context["last_recommended_dishes"]
        ):
            break

    return context


# =========================================================
# FOLLOW-UP HANDLER  (FIXED)
# =========================================================

FOLLOW_UP_KEYWORDS = [
    "more details",
    "details",
    "tell me more",
    "more",
    "price",
    "ingredients",
    "is it spicy",
    "what comes with it",
    "describe it",
]

AFFIRMATIVE_KEYWORDS = [
    "yes",
    "yeah",
    "yep",
    "sure",
    "ok",
    "okay",
    "go ahead",
    "please",
    "do it",
]


def enhance_message_with_context(
    message,
    context,
):

    text = normalize(message)

    last_dish = context.get("last_dish")
    last_category = context.get("last_category")
    last_intent = context.get("last_intent")
    last_recommended_dishes = context.get("last_recommended_dishes", [])

    # Build a readable list of recently recommended dishes
    # e.g. "Grilled Chicken and Vanilla Ice Cream"
    recommended_label = (
        " and ".join(last_recommended_dishes)
        if last_recommended_dishes
        else None
    )

    # =====================================================
    # YES / AFFIRMATIVE HANDLING  (FIXED)
    # Previously fell through when last_dish was None,
    # sending raw "yes" to GPT with no context.
    # Now has layered fallbacks so context is always clear.
    # =====================================================

    if text in AFFIRMATIVE_KEYWORDS:

        # Best case: we know the exact last dish
        if last_dish:
            return (
                f"Tell me more details about {last_dish}, "
                f"including its description, ingredients, "
                f"price, and any recommendations."
            )

        # Good case: we know multiple recommended dishes
        if recommended_label:
            return (
                f"Tell me more details about "
                f"{recommended_label}, including their "
                f"descriptions, ingredients, prices, "
                f"and any recommendations."
            )

        # Fallback: we know the category
        if last_category:
            return (
                f"Recommend more dishes from the "
                f"{last_category} category with details."
            )

        # Last resort: ask GPT to elaborate on whatever it last said
        return (
            "Please give more details about the items "
            "you just recommended, including descriptions, "
            "ingredients, and prices."
        )

    # =====================================================
    # DETAILS HANDLING  (FIXED)
    # =====================================================

    if any(kw in text for kw in FOLLOW_UP_KEYWORDS):

        if last_dish:

            return (
                f"Give full details about "
                f"{last_dish} including "
                f"description, ingredients, "
                f"price and recommendations."
            )

        if recommended_label:
            return (
                f"Give full details about {recommended_label} "
                f"including descriptions, ingredients, "
                f"prices and recommendations."
            )

    # =====================================================
    # PRICE FOLLOW-UP
    # =====================================================

    if (
        "price" in text
        and last_dish
    ):

        return (
            f"What is the price of "
            f"{last_dish}?"
        )

    if "price" in text and recommended_label:
        return f"What are the prices of {recommended_label}?"

    # =====================================================
    # INGREDIENT FOLLOW-UP
    # =====================================================

    if (
        "ingredient" in text
        and last_dish
    ):

        return (
            f"What ingredients are in "
            f"{last_dish}?"
        )

    if "ingredient" in text and recommended_label:
        return f"What ingredients are in {recommended_label}?"

    # =====================================================
    # CHEAPEST / EXPENSIVE
    # =====================================================

    if (
        "cheapest" in text
        and last_category
    ):

        return (
            f"What is the cheapest dish "
            f"in {last_category} category?"
        )

    if (
        "expensive" in text
        and last_category
    ):

        return (
            f"What is the most expensive dish "
            f"in {last_category} category?"
        )

    return message


# =========================================================
# MENU SEARCH
# =========================================================

def search_menu_items(
    keywords: Optional[List[str]] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    available_only: bool = True,
    limit: int = 10,
):

    query = Q()

    queryset = MenuItem.objects.select_related(
        "category"
    )

    if keywords:

        for word in keywords:

            query |= (
                Q(name__icontains=word)
                | Q(description__icontains=word)
                | Q(ingredients__icontains=word)
                | Q(category__name__icontains=word)
            )

        queryset = queryset.filter(query)

    if category:

        queryset = queryset.filter(
            category__name__icontains=category
        )

    if min_price is not None:

        queryset = queryset.filter(
            price__gte=min_price
        )

    if max_price is not None:

        queryset = queryset.filter(
            price__lte=max_price
        )

    if available_only:

        queryset = queryset.filter(
            availability=True
        )

    queryset = queryset.distinct()[:limit]

    return [
        {
            "id": item.id,
            "name": item.name,
            "category": item.category.name,
            "price": money(item.price),
            "description": item.description or "",
            "ingredients": item.ingredients or "",
        }
        for item in queryset
    ]


# =========================================================
# POPULAR DISHES
# =========================================================

def get_most_ordered_dishes(limit=5):

    rows = (
        OrderItem.objects
        .values(
            "menu_item__name",
            "menu_item__category__name",
        )
        .annotate(
            total_orders=Count("id"),
            total_quantity=Sum("quantity"),
        )
        .order_by("-total_quantity")[:limit]
    )

    return [
        {
            "dish": row["menu_item__name"],
            "category": row["menu_item__category__name"],
            "quantity_sold": row["total_quantity"],
        }
        for row in rows
    ]


# =========================================================
# RECOMMENDATIONS
# =========================================================

def get_personalized_recommendations(
    user,
    limit=5,
):

    if not user or not user.is_authenticated:
        return get_most_ordered_dishes(limit)

    favorite_categories = (
        FavoriteMenuItem.objects
        .filter(user=user)
        .values("menu_item__category__name")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    category_names = [
        x["menu_item__category__name"]
        for x in favorite_categories
    ]

    items = (
        MenuItem.objects
        .select_related("category")
        .filter(
            category__name__in=category_names,
            availability=True,
        )[:limit]
    )

    return [
        {
            "name": item.name,
            "category": item.category.name,
            "price": money(item.price),
        }
        for item in items
    ]


# =========================================================
# TOOLS
# =========================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_menu",
            "description": "Search menu items",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                    },
                    "category": {
                        "type": "string"
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_popular_dishes",
            "description": "Get popular dishes",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recommendations",
            "description": "Get recommendations",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]


# =========================================================
# TOOL EXECUTION
# =========================================================

def execute_tool(
    tool_name,
    arguments,
    user,
):

    if tool_name == "search_menu":

        return search_menu_items(
            keywords=arguments.get("keywords"),
            category=arguments.get("category"),
        )

    if tool_name == "get_popular_dishes":

        return get_most_ordered_dishes()

    if tool_name == "get_recommendations":

        return get_personalized_recommendations(
            user
        )

    return {
        "error": "Unknown tool"
    }


# =========================================================
# SYSTEM PROMPT
# =========================================================

def build_system_prompt(user):

    role = "guest"

    if user and user.is_authenticated:
        role = user.role

    return f"""
You are an intelligent restaurant AI assistant.

IMPORTANT RULES:

- ALWAYS maintain conversation continuity
- ALWAYS understand follow-up questions
- NEVER ask unnecessary clarification questions
- If the user says:
  "more details"
  "price"
  "ingredients"
  "is it spicy"
  "tell me more"
  → refer to the LAST discussed dish

- Be natural and conversational
- NEVER hallucinate menu items
- ONLY use provided tool/database results
- Understand spelling mistakes naturally
- Keep responses concise but useful

Current user role: {role}
"""


# =========================================================
# MAIN CHATBOT
# =========================================================

def ask_chatbot(
    user,
    message,
    session_id=None,
):

    conversation_key = get_conversation_key(
        user,
        session_id,
    )

    # =====================================================
    # LOAD HISTORY
    # =====================================================

    history = get_conversation_history(
        conversation_key
    )

    # =====================================================
    # EXTRACT CONTEXT
    # =====================================================

    context = extract_context_from_history(
        history
    )

    # =====================================================
    # ENHANCE FOLLOW-UP MESSAGE
    # =====================================================

    enhanced_message = (
        enhance_message_with_context(
            message,
            context,
        )
    )

    # =====================================================
    # SAVE USER MESSAGE
    # =====================================================

    user_message = {
        "role": "user",
        "content": enhanced_message,
    }

    save_message(
        conversation_key,
        user_message,
    )

    # =====================================================
    # BUILD MESSAGE LIST
    # =====================================================

    history = get_conversation_history(
        conversation_key
    )

    messages = [
        {
            "role": "system",
            "content": build_system_prompt(user),
        }
    ]

    messages.extend(history)

    # =====================================================
    # FIRST RESPONSE
    # =====================================================

    first_response = (
        client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
    )

    response_message = (
        first_response
        .choices[0]
        .message
    )

    tool_calls = response_message.tool_calls

    # =====================================================
    # TOOL FLOW
    # =====================================================

    if tool_calls:

        messages.append(response_message)

        save_message(
            conversation_key,
            response_message.model_dump(),
        )

        for tool_call in tool_calls:

            tool_name = (
                tool_call.function.name
            )

            arguments = json.loads(
                tool_call.function.arguments
            )

            result = execute_tool(
                tool_name,
                arguments,
                user,
            )

            tool_message = {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": tool_name,
                "content": json.dumps(result),
            }

            messages.append(tool_message)

            save_message(
                conversation_key,
                tool_message,
            )

        final_response = (
            client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=messages,
            )
        )

        final_text = (
            final_response
            .choices[0]
            .message
            .content
        )

        save_message(
            conversation_key,
            {
                "role": "assistant",
                "content": final_text,
            }
        )

        return final_text

    # =====================================================
    # NORMAL RESPONSE
    # =====================================================

    final_text = response_message.content

    save_message(
        conversation_key,
        {
            "role": "assistant",
            "content": final_text,
        }
    )

    return final_text


# =========================================================
# RESET CHAT
# =========================================================

def reset_chat(
    user,
    session_id=None,
):

    conversation_key = get_conversation_key(
        user,
        session_id,
    )

    clear_conversation(
        conversation_key
    )

    return {
        "success": True,
        "message": "Conversation reset successfully",
    }