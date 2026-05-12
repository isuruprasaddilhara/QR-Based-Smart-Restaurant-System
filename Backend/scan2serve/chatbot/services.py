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
    F,
    ExpressionWrapper,
    DecimalField,
)

from openai import OpenAI

from menu.models import MenuItem, MenuCategory
from orders.models import Order, OrderItem, Feedback
from favourites.models import FavoriteMenuItem
from tables.models import Table

client = OpenAI(api_key=settings.OPENAI_API_KEY)

# =========================================================
# MEMORY STORAGE
# =========================================================

# production -> use redis/database
CONVERSATION_MEMORY = defaultdict(list)

MAX_HISTORY = 50


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
    """
    Store FULL message objects
    """

    CONVERSATION_MEMORY[conversation_key].append(message)

    CONVERSATION_MEMORY[conversation_key] = (
        CONVERSATION_MEMORY[conversation_key][-MAX_HISTORY:]
    )


def get_conversation_history(conversation_key):
    return CONVERSATION_MEMORY.get(conversation_key, [])


def clear_conversation(conversation_key):
    CONVERSATION_MEMORY[conversation_key] = []


# =========================================================
# CONTEXT EXTRACTION
# =========================================================

def extract_context_from_history(history):

    context = {
        "last_dish": None,
        "last_category": None,
        "last_intent": None,
    }

    combined_text = " ".join(
        [
            str(msg.get("content", ""))
            for msg in history
            if msg.get("content")
        ]
    ).lower()

    # categories
    categories = MenuCategory.objects.values_list(
        "name",
        flat=True,
    )

    for category in categories:
        if category.lower() in combined_text:
            context["last_category"] = category

    # menu items
    items = MenuItem.objects.all()[:200]

    for item in items:
        if item.name.lower() in combined_text:
            context["last_dish"] = item.name

    # intent detection
    if (
        "recommend" in combined_text
        or "suggest" in combined_text
    ):
        context["last_intent"] = "recommendation"

    elif "price" in combined_text:
        context["last_intent"] = "pricing"

    elif "ingredient" in combined_text:
        context["last_intent"] = "ingredients"

    elif "order" in combined_text:
        context["last_intent"] = "orders"

    return context


# =========================================================
# FOLLOW-UP QUESTION HANDLER
# =========================================================

def enhance_message_with_context(message, context):

    text = message.lower().strip()

    # yes/no handling
    if text in ["yes", "yeah", "yep", "sure", "ok"]:

        if context["last_intent"] == "recommendation":
            return (
                "Please recommend similar dishes "
                "based on the previous conversation."
            )

    if (
        "cheapest" in text
        and context["last_category"]
    ):
        return (
            f"Which item in category "
            f"{context['last_category']} "
            f"is cheapest?"
        )

    if (
        "most expensive" in text
        and context["last_category"]
    ):
        return (
            f"Which item in category "
            f"{context['last_category']} "
            f"is most expensive?"
        )

    if (
        "ingredients" in text
        and context["last_dish"]
    ):
        return (
            f"What are the ingredients of "
            f"{context['last_dish']}?"
        )

    if (
        "price" in text
        and context["last_dish"]
    ):
        return (
            f"What is the price of "
            f"{context['last_dish']}?"
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
    ingredients: Optional[List[str]] = None,
    limit: int = 20,
):

    query = Q()

    if keywords:
        for word in keywords:
            query |= (
                Q(name__icontains=word)
                | Q(description__icontains=word)
                | Q(ingredients__icontains=word)
                | Q(category__name__icontains=word)
            )

    queryset = MenuItem.objects.select_related(
        "category"
    )

    if keywords:
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

    if ingredients:

        ingredient_query = Q()

        for ingredient in ingredients:
            ingredient_query |= Q(
                ingredients__icontains=ingredient
            )

        queryset = queryset.filter(
            ingredient_query
        )

    queryset = queryset.distinct()[:limit]

    return [
        {
            "id": item.id,
            "name": item.name,
            "category": item.category.name,
            "price": money(item.price),
            "available": item.availability,
            "description": item.description or "",
            "ingredients": item.ingredients or "",
            "image_url": item.image_url or "",
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
            "menu_item__id",
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
            "times_ordered": row["total_orders"],
            "quantity_sold": row["total_quantity"],
        }
        for row in rows
    ]


# =========================================================
# TOP RATED
# =========================================================

def get_top_rated_dishes(limit=5):

    rows = (
        MenuItem.objects
        .annotate(
            avg_rating=Avg(
                "orderitem__order__feedback__rating"
            ),
            review_count=Count(
                "orderitem__order__feedback"
            ),
        )
        .filter(review_count__gt=0)
        .order_by(
            "-avg_rating",
            "-review_count",
        )[:limit]
    )

    return [
        {
            "name": item.name,
            "rating": round(item.avg_rating or 0, 2),
            "reviews": item.review_count,
            "price": money(item.price),
        }
        for item in rows
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

    if category_names:

        items = (
            MenuItem.objects
            .select_related("category")
            .filter(
                category__name__in=category_names,
                availability=True,
            )[:limit]
        )

    else:

        items = (
            MenuItem.objects
            .select_related("category")
            .filter(
                availability=True
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
# TOOL DEFINITIONS
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
                    "min_price": {
                        "type": "number"
                    },
                    "max_price": {
                        "type": "number"
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
            "name": "get_top_rated",
            "description": "Get top rated dishes",
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
            min_price=arguments.get("min_price"),
            max_price=arguments.get("max_price"),
        )

    if tool_name == "get_popular_dishes":
        return get_most_ordered_dishes()

    if tool_name == "get_top_rated":
        return get_top_rated_dishes()

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
You are an advanced AI restaurant assistant.

Rules:
- ONLY use provided database facts
- NEVER hallucinate dishes, prices, ratings, or analytics
- If information is unavailable, clearly say so
- Be conversational and friendly
- ALWAYS understand follow-up messages
- NEVER restart the conversation unnecessarily
- If the user says "yes", "okay", "sure", or similar,
  continue from previous context naturally
- Use previous messages to understand intent
- Recommend dishes intelligently
- Personalize responses when possible
- give answers even if user provide with spelling mistakes and short names (eg: "piz" for "pizza" or "coke" for "coca-cola" or vegi for vegetarian)
- Answer with commen sense and suggestions to make the conversation more engaging and natural

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

    # load previous history
    history = get_conversation_history(
        conversation_key
    )

    # extract context
    history_context = (
        extract_context_from_history(
            history
        )
    )

    # enhance follow-up questions
    enhanced_message = (
        enhance_message_with_context(
            message,
            history_context,
        )
    )

    # save user message
    save_message(
        conversation_key,
        {
            "role": "user",
            "content": enhanced_message,
        }
    )

    # rebuild history
    history = get_conversation_history(
        conversation_key
    )

    messages = [
        {
            "role": "system",
            "content": build_system_prompt(user),
        }
    ]

    # inject memory
    messages.extend(history)

    # =====================================================
    # FIRST RESPONSE
    # =====================================================

    first_response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    response_message = (
        first_response
        .choices[0]
        .message
    )

    tool_calls = response_message.tool_calls

    # =====================================================
    # TOOL CALL FLOW
    # =====================================================

    if tool_calls:

        # append assistant tool call
        messages.append(response_message)

        # save assistant tool call
        save_message(
            conversation_key,
            response_message.model_dump()
        )

        for tool_call in tool_calls:

            tool_name = tool_call.function.name

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

            # save tool response
            save_message(
                conversation_key,
                tool_message
            )

        # =================================================
        # FINAL RESPONSE
        # =================================================

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

        # save final assistant message
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

    conversation_key = (
        get_conversation_key(
            user,
            session_id,
        )
    )

    clear_conversation(
        conversation_key
    )

    return {
        "success": True,
        "message": "Conversation reset successfully",
    }