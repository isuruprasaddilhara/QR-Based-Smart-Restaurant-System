# services.py  —  Unified Restaurant Chatbot Service
# Merges structured-context (v1) + memory/tool-calling (v2)

import json
from collections import defaultdict
from decimal import Decimal
from typing import Dict, List, Optional

from django.conf import settings
from django.db.models import Avg, Count, Q, Sum

from openai import OpenAI

from menu.models import MenuItem, MenuCategory
from orders.models import Order, OrderItem, Feedback
from favourites.models import FavoriteMenuItem

client = OpenAI(api_key=settings.OPENAI_API_KEY)


# =========================================================
# CONVERSATION MEMORY
# =========================================================

CONVERSATION_MEMORY: Dict[str, list] = defaultdict(list)
MAX_HISTORY = 30


def get_conversation_key(user, session_id=None) -> str:
    if user and user.is_authenticated:
        return f"user_{user.id}"
    if session_id:
        return f"guest_{session_id}"
    return "anonymous"


def save_message(conversation_key: str, message: dict) -> None:
    CONVERSATION_MEMORY[conversation_key].append(message)
    CONVERSATION_MEMORY[conversation_key] = (
        CONVERSATION_MEMORY[conversation_key][-MAX_HISTORY:]
    )


def get_conversation_history(conversation_key: str) -> list:
    return CONVERSATION_MEMORY.get(conversation_key, [])


def clear_conversation(conversation_key: str) -> None:
    CONVERSATION_MEMORY[conversation_key] = []


# =========================================================
# SMALL HELPERS
# =========================================================

def money(value) -> str:
    if value is None:
        return "0.00"
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    return str(value)


def normalize(text: str) -> str:
    return (text or "").strip().lower()


def contains_any(text: str, words: List[str]) -> bool:
    t = normalize(text)
    return any(w in t for w in words)


def extract_keywords(message: str) -> List[str]:
    cleaned = (
        normalize(message)
        .replace(",", " ").replace(".", " ")
        .replace("?", " ").replace("!", " ")
        .replace("-", " ")
    )
    words = [w.strip() for w in cleaned.split() if len(w.strip()) >= 3]
    return list(dict.fromkeys(words))


# =========================================================
# MENU QUERIES
# =========================================================

def find_matching_menu_items(message: str):
    keywords = extract_keywords(message)
    if not keywords:
        return MenuItem.objects.none()

    query = Q()
    for word in keywords:
        query |= Q(name__icontains=word)
        query |= Q(description__icontains=word)
        query |= Q(ingredients__icontains=word)
        query |= Q(category__name__icontains=word)

    return (
        MenuItem.objects
        .select_related("category")
        .filter(query)
        .distinct()
    )


def get_available_menu_items(limit: int = 15) -> List[Dict]:
    items = (
        MenuItem.objects
        .select_related("category")
        .filter(availability=True)
        .order_by("category__name", "name")[:limit]
    )
    return [
        {
            "name": item.name,
            "category": item.category.name,
            "price": money(item.price),
            "ingredients": item.ingredients or "N/A",
            "description": item.description or "N/A",
        }
        for item in items
    ]


def get_menu_item_details(message: str) -> List[Dict]:
    items = find_matching_menu_items(message)[:10]
    return [
        {
            "name": item.name,
            "category": item.category.name,
            "price": money(item.price),
            "available": item.availability,
            "ingredients": item.ingredients or "N/A",
            "description": item.description or "N/A",
        }
        for item in items
    ]


def get_menu_categories() -> List[str]:
    return list(
        MenuCategory.objects.order_by("name").values_list("name", flat=True)
    )


def search_menu_items(
    keywords: Optional[List[str]] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    available_only: bool = True,
    limit: int = 10,
) -> List[Dict]:
    """Full-featured menu search used by tool calls."""
    query = Q()
    queryset = MenuItem.objects.select_related("category")

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
        queryset = queryset.filter(category__name__icontains=category)
    if min_price is not None:
        queryset = queryset.filter(price__gte=min_price)
    if max_price is not None:
        queryset = queryset.filter(price__lte=max_price)
    if available_only:
        queryset = queryset.filter(availability=True)

    queryset = queryset.distinct()[:limit]

    return [
        {
            "id": item.id,
            "name": item.name,
            "category": item.category.name,
            "price": money(item.price),
            "description": item.description or "",
            "ingredients": item.ingredients or "",
            "available": item.availability,
        }
        for item in queryset
    ]


# =========================================================
# ANALYTICS / CALCULATIONS
# =========================================================

def get_most_ordered_dishes(limit: int = 5) -> List[Dict]:
    rows = (
        OrderItem.objects
        .values("menu_item__id", "menu_item__name", "menu_item__category__name")
        .annotate(
            order_count=Count("id"),
            total_quantity=Sum("quantity"),
        )
        .order_by("-total_quantity")[:limit]
    )

    dish_ids = [row["menu_item__id"] for row in rows]
    items = MenuItem.objects.filter(id__in=dish_ids).select_related("category")
    item_map = {item.id: item for item in items}

    result = []
    for row in rows:
        item = item_map.get(row["menu_item__id"])
        if item:
            result.append({
                "name": item.name,
                "price": money(item.price),
                "category": item.category.name,
                "description": item.description or "",
                "times_ordered": row["order_count"],
                "quantity_sold": row["total_quantity"],
            })
    return result


def get_top_rated_dishes(limit: int = 5, min_reviews: int = 1) -> List[Dict]:
    rows = (
        MenuItem.objects
        .filter(orderitem__order__feedback__isnull=False)
        .annotate(
            avg_rating=Avg("orderitem__order__feedback__rating"),
            review_count=Count("orderitem__order__feedback"),
        )
        .filter(review_count__gte=min_reviews)
        .order_by("-avg_rating", "-review_count", "name")[:limit]
    )
    return [
        {
            "name": item.name,
            "avg_rating": round(item.avg_rating or 0, 2),
            "review_count": item.review_count or 0,
            "price": money(item.price),
        }
        for item in rows
    ]


def get_order_stats() -> Dict:
    total_sales = (
        Order.objects.filter(status="completed")
        .aggregate(total=Sum("total_amount"))
        .get("total") or Decimal("0.00")
    )
    avg_feedback = Feedback.objects.aggregate(avg=Avg("rating")).get("avg")

    return {
        "total_orders": Order.objects.count(),
        "completed_orders": Order.objects.filter(status="completed").count(),
        "pending_orders": Order.objects.filter(status="pending").count(),
        "preparing_orders": Order.objects.filter(status="preparing").count(),
        "served_orders": Order.objects.filter(status="served").count(),
        "total_sales": money(total_sales),
        "average_feedback_rating": (
            round(avg_feedback, 2) if avg_feedback is not None else None
        ),
    }


# =========================================================
# CUSTOMER-SPECIFIC QUERIES
# =========================================================

def get_user_recent_orders(user, limit: int = 5) -> List[Dict]:
    if not user or not user.is_authenticated:
        return []

    orders = (
        Order.objects
        .select_related("table")
        .prefetch_related("items__menu_item")
        .filter(user=user)
        .order_by("-created_at")[:limit]
    )

    data = []
    for order in orders:
        items = [
            {
                "name": oi.menu_item.name,
                "quantity": oi.quantity,
                "line_total": money(oi.price),
            }
            for oi in order.items.all()
        ]
        data.append({
            "order_id": order.id,
            "status": order.status,
            "total_amount": money(order.total_amount),
            "table_id": order.table.id if order.table else None,
            "special_notes": order.special_notes or "",
            "created_at": str(order.created_at),
            "items": items,
        })
    return data


def get_personalized_recommendations(user, limit: int = 5) -> List[Dict]:
    if not user or not user.is_authenticated:
        return get_most_ordered_dishes(limit)

    favorite_categories = (
        FavoriteMenuItem.objects
        .filter(user=user)
        .values("menu_item__category__name")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    category_names = [x["menu_item__category__name"] for x in favorite_categories]

    items = (
        MenuItem.objects
        .select_related("category")
        .filter(category__name__in=category_names, availability=True)[:limit]
    )
    return [
        {
            "name": item.name,
            "category": item.category.name,
            "price": money(item.price),
            "description": item.description or "",
        }
        for item in items
    ]


# =========================================================
# CONVERSATION CONTEXT EXTRACTION
# =========================================================

def _extract_text_from_message(msg: dict) -> str:
    """Safely extract searchable text from any message type."""
    role = msg.get("role", "")
    raw = msg.get("content")

    if role == "tool" and raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return " ".join(
                    f"{item.get('name', '')} "
                    f"{item.get('description', '')} "
                    f"{item.get('category', '')}"
                    for item in parsed
                ).lower().strip()
            if isinstance(parsed, dict):
                return (
                    f"{parsed.get('name', '')} "
                    f"{parsed.get('description', '')}"
                ).lower().strip()
        except (json.JSONDecodeError, AttributeError):
            return normalize(str(raw))

    if raw and isinstance(raw, str):
        return normalize(raw)

    return ""


def extract_context_from_history(history: list) -> Dict:
    context = {
        "last_dish": None,
        "last_category": None,
        "last_intent": None,
        "last_recommended_dishes": [],
    }

    recent_messages = history[-10:]
    all_items = list(MenuItem.objects.select_related("category").all())
    all_categories = list(MenuCategory.objects.all())

    for msg in reversed(recent_messages):
        role = msg.get("role", "")
        content = _extract_text_from_message(msg)
        if not content:
            continue

        if not context["last_dish"]:
            for item in all_items:
                if item.name.lower() in content:
                    context["last_dish"] = item.name
                    break

        if role in ("assistant", "tool") and not context["last_recommended_dishes"]:
            mentioned = [
                item.name for item in all_items
                if item.name.lower() in content
            ]
            if mentioned:
                context["last_recommended_dishes"] = mentioned

        if not context["last_category"]:
            for category in all_categories:
                if category.name.lower() in content:
                    context["last_category"] = category.name
                    break

        if not context["last_intent"]:
            if contains_any(content, ["recommend", "suggest", "popular", "best"]):
                context["last_intent"] = "recommendation"
            elif contains_any(content, ["price", "cost", "expensive", "cheap"]):
                context["last_intent"] = "pricing"
            elif contains_any(content, ["ingredient", "contains", "made of"]):
                context["last_intent"] = "ingredients"
            elif contains_any(content, ["detail", "more", "describe"]):
                context["last_intent"] = "details"

        if all([
            context["last_dish"],
            context["last_category"],
            context["last_intent"],
            context["last_recommended_dishes"],
        ]):
            break

    return context


# =========================================================
# FOLLOW-UP / MESSAGE ENHANCEMENT
# =========================================================

FOLLOW_UP_KEYWORDS = [
    "more details", "details", "tell me more", "more",
    "price", "ingredients", "is it spicy",
    "what comes with it", "describe it",
]

AFFIRMATIVE_KEYWORDS = [
    "yes", "yeah", "yep", "sure", "ok",
    "okay", "go ahead", "please", "do it",
]


def enhance_message_with_context(message: str, context: Dict) -> str:
    text = normalize(message)

    last_dish = context.get("last_dish")
    last_category = context.get("last_category")
    last_recommended_dishes = context.get("last_recommended_dishes", [])
    recommended_label = (
        " and ".join(last_recommended_dishes) if last_recommended_dishes else None
    )

    # --- Affirmative ---
    if text in AFFIRMATIVE_KEYWORDS:
        if last_dish:
            return (
                f"Tell me more details about {last_dish}, "
                f"including its description, ingredients, price, and recommendations."
            )
        if recommended_label:
            return (
                f"Tell me more details about {recommended_label}, "
                f"including descriptions, ingredients, prices, and recommendations."
            )
        if last_category:
            return f"Recommend more dishes from the {last_category} category with details."
        return "Please give more details about the items you just recommended."

    # --- Details follow-up ---
    if any(kw in text for kw in FOLLOW_UP_KEYWORDS):
        if last_dish:
            return (
                f"Give full details about {last_dish} including "
                f"description, ingredients, price and recommendations."
            )
        if recommended_label:
            return (
                f"Give full details about {recommended_label} including "
                f"descriptions, ingredients, prices and recommendations."
            )

    # --- Price follow-up ---
    if "price" in text:
        if last_dish:
            return f"What is the price of {last_dish}?"
        if recommended_label:
            return f"What are the prices of {recommended_label}?"

    # --- Ingredient follow-up ---
    if "ingredient" in text:
        if last_dish:
            return f"What ingredients are in {last_dish}?"
        if recommended_label:
            return f"What ingredients are in {recommended_label}?"

    # --- Cheapest / most expensive ---
    if "cheapest" in text and last_category:
        return f"What is the cheapest dish in the {last_category} category?"
    if "expensive" in text and last_category:
        return f"What is the most expensive dish in the {last_category} category?"

    return message


# =========================================================
# INTENT DETECTION  (for pre-fetching context)
# =========================================================

def detect_intent(message: str) -> str:
    text = normalize(message)

    if contains_any(text, [
        "most ordered", "popular dish", "popular dishes",
        "best selling", "top selling", "most popular",
    ]):
        return "popular_dishes"

    if contains_any(text, [
        "top rated", "best rated", "highest rated", "best dish",
    ]):
        return "top_rated_dishes"

    if contains_any(text, [
        "ingredient", "ingredients", "what is in", "contains", "content of",
    ]):
        return "dish_contents"

    if contains_any(text, ["price", "cost", "how much"]):
        return "dish_price"

    if contains_any(text, [
        "available", "availability", "do you have", "show menu",
    ]):
        return "menu_lookup"

    if contains_any(text, ["category", "categories"]):
        return "categories"

    if contains_any(text, [
        "my order", "my orders", "order status",
        "recent orders", "my recent order",
    ]):
        return "user_orders"

    if contains_any(text, [
        "sales", "total orders", "order stats",
        "statistics", "analytics",
    ]):
        return "order_stats"

    if contains_any(text, ["recommend", "suggest", "what should i"]):
        return "recommendations"

    return "general_lookup"


# =========================================================
# OPENAI TOOL DEFINITIONS
# =========================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_menu",
            "description": (
                "Search menu items by keywords, category, or price range. "
                "Use for questions about specific dishes, ingredients, prices, "
                "availability, or browsing the menu."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Words to search for in name, description, ingredients",
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by category name",
                    },
                    "min_price": {
                        "type": "number",
                        "description": "Minimum price filter",
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Maximum price filter",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_popular_dishes",
            "description": (
                "Get the most ordered / best-selling dishes. "
                "Use when user asks for popular, trending, or top dishes."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_rated_dishes",
            "description": (
                "Get highest rated dishes based on customer feedback. "
                "Use when user asks for best-rated or top-reviewed dishes."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recommendations",
            "description": (
                "Get personalized dish recommendations for the user. "
                "Uses favourites for logged-in users, otherwise popular dishes."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_orders",
            "description": (
                "Retrieve the current user's recent orders and their status. "
                "Use for 'my orders', 'order status', or 'what did I order'."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_stats",
            "description": (
                "Get restaurant-wide order statistics, sales totals, and "
                "average feedback rating. Use for analytics or admin queries."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_menu_categories",
            "description": "List all available menu categories.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


# =========================================================
# TOOL EXECUTION
# =========================================================

def execute_tool(tool_name: str, arguments: dict, user) -> any:
    if tool_name == "search_menu":
        return search_menu_items(
            keywords=arguments.get("keywords"),
            category=arguments.get("category"),
            min_price=arguments.get("min_price"),
            max_price=arguments.get("max_price"),
        )

    if tool_name == "get_popular_dishes":
        return get_most_ordered_dishes()

    if tool_name == "get_top_rated_dishes":
        return get_top_rated_dishes()

    if tool_name == "get_recommendations":
        return get_personalized_recommendations(user)

    if tool_name == "get_user_orders":
        return get_user_recent_orders(user)

    if tool_name == "get_order_stats":
        return {
            "stats": get_order_stats(),
            "most_ordered": get_most_ordered_dishes(3),
            "top_rated": get_top_rated_dishes(3),
        }

    if tool_name == "get_menu_categories":
        return get_menu_categories()

    return {"error": f"Unknown tool: {tool_name}"}


# =========================================================
# SYSTEM PROMPT
# =========================================================

FAQ_TEXT = """
--- FREQUENTLY ASKED QUESTIONS ---

Category 1 — Using Scan2Serve (app, orders & service)
Q: How do I place an order?
A: Open the menu, add dishes to your cart, go to checkout, enter your table number if asked, and confirm.
Q: Can I order as a guest?
A: Yes. An account can help with past orders and more personalised chat answers.
Q: Why do you need my table number?
A: So staff know where to bring your food.
Q: The menu link or QR code doesn't work.
A: Check your connection, refresh, or ask staff for a new QR or link.
Q: How do I track my order?
A: Use Track My Order in the chat or the track-order screen.
Q: Why does the chat ask me to log in?
A: Questions about your order history may require a logged-in account.
Q: Can I change my order after I submit it?
A: It depends on the restaurant and how far preparation has gone. Use chat or ask staff.
Q: Something is wrong with my order (wrong or missing item).
A: Share your table and order details here, or speak to staff so they can fix it quickly.
Q: How do I pay? / Will I get a receipt?
A: Follow on-screen checkout or pay as the location instructs. Receipts may be in-app, by email, or from staff.
Q: The app is slow or won't load.
A: Try reopening the link, switching network, or updating the browser.
Q: Who do I contact for support?
A: Use this chat for app issues; ask the restaurant directly for on-site policies or billing.

Category 2 — Food, allergens & dietary needs
Q: Is this dish gluten-free?
A: Treat menu labels as a guide; recipes can change. Confirm with staff for strict needs.
Q: Do you have a gluten-free menu?
A: Look for marked items or ask staff; some dishes can be changed, others cannot.
Q: Is it dairy-free / lactose-free?
A: Check descriptions and allergen notes, then confirm with staff—many sauces contain dairy.
Q: Can you make it without egg?
A: Only if the dish allows it. Add a clear note; staff may suggest another item.
Q: Does this contain nuts or peanuts? Is the kitchen nut-free?
A: Use on-item allergen info if shown, and always ask staff. Most kitchens are not nut-free.
Q: Is this vegan? / Can vegetarian be made vegan?
A: Check labels; vegetarian is not always vegan. Notes help; staff may suggest swaps.
Q: Is the food halal / kosher certified?
A: It varies by restaurant. Look for certification on the menu or ask staff.
Q: Is this spicy? Can you make it mild?
A: Check the menu; add "mild" or "extra spicy" in special notes when possible.
Q: Low salt / no MSG / diabetic-friendly?
A: Put your needs in the notes; staff can advise if the dish can be adjusted.
Q: What if I have a severe allergy?
A: Always speak to staff in person before ordering; online notes are not enough for severe allergies.

Allergen disclaimer: Information comes from the restaurant and may change. When in doubt, ask staff before ordering.
"""


def build_system_prompt(user) -> str:
    role = "guest"
    if user and user.is_authenticated:
        role = getattr(user, "role", "customer")

    return f"""You are an intelligent restaurant AI assistant for Scan2Serve.

STRICT RULES:
- NEVER invent dishes, prices, ingredients, ratings, or order details.
- ONLY use data returned by tool calls or explicitly provided.
- If data is missing, say so clearly and honestly.
- Understand spelling mistakes naturally; do not ask for clarification unnecessarily.
- ALWAYS maintain conversation continuity and understand follow-up questions.
- If the user says "more details", "price", "ingredients", "tell me more", or similar,
  refer to the LAST discussed dish or the dishes just recommended.
- Be concise, friendly, and accurate. Mention multiple matches clearly.
- If user types "frequently asked questions" or "FAQ", return the full FAQ below.

{FAQ_TEXT}

Current user role: {role}
"""


# =========================================================
# MAIN CHATBOT  —  tool-calling loop with memory
# =========================================================

def ask_chatbot(user, message: str, session_id=None) -> str:
    conversation_key = get_conversation_key(user, session_id)

    # 1. Load history and extract conversational context
    history = get_conversation_history(conversation_key)
    context = extract_context_from_history(history)

    # 2. Enhance short follow-ups with resolved dish/category names
    enhanced_message = enhance_message_with_context(message, context)

    # 3. Save (enhanced) user message
    user_msg = {"role": "user", "content": enhanced_message}
    save_message(conversation_key, user_msg)

    # 4. Build full message list for the API
    history = get_conversation_history(conversation_key)
    messages = [{"role": "system", "content": build_system_prompt(user)}]
    messages.extend(history)

    # 5. First API call — may trigger tool use
    first_response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    response_message = first_response.choices[0].message
    tool_calls = response_message.tool_calls

    # 6. Tool-calling loop
    if tool_calls:
        # Append assistant's tool-use message to history
        messages.append(response_message)
        save_message(conversation_key, response_message.model_dump())

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            result = execute_tool(tool_name, arguments, user)

            tool_msg = {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": tool_name,
                "content": json.dumps(result),
            }
            messages.append(tool_msg)
            save_message(conversation_key, tool_msg)

        # Final response after tools
        final_response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
        )
        final_text = final_response.choices[0].message.content

    else:
        # Direct answer — no tools needed
        final_text = response_message.content

    # 7. Save assistant reply and return
    save_message(conversation_key, {"role": "assistant", "content": final_text})
    return final_text


# =========================================================
# RESET CHAT
# =========================================================

def reset_chat(user, session_id=None) -> Dict:
    conversation_key = get_conversation_key(user, session_id)
    clear_conversation(conversation_key)
    return {"success": True, "message": "Conversation reset successfully."}