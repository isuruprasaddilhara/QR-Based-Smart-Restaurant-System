from decimal import Decimal
from typing import Dict, List, Optional

from django.conf import settings
from django.db.models import Avg, Count, Q, Sum
from openai import OpenAI

from menu.models import MenuItem, MenuCategory
from orders.models import Order, OrderItem, Feedback

client = OpenAI(api_key=settings.OPENAI_API_KEY)


# ============================================================
# INTENT MAP  –  single source of truth for keyword routing
# ============================================================

INTENT_MAP: Dict[str, List[str]] = {
    "popular_dishes":     [
        "most ordered", "popular dish", "popular dishes", "best selling",
        "top selling", "most popular", "most ordered dish", "what sells",
    ],
    "top_rated_dishes":   [
        "top rated", "best rated", "highest rated", "best dish",
        "most loved", "customer favourite", "fan favourite",
    ],
    "dish_contents":      [
        "ingredient", "ingredients", "what is in", "what's in",
        "contains", "content of", "made of", "made with",
    ],
    "dietary":            [
        "vegan", "vegetarian", "gluten", "halal", "kosher",
        "spicy", "dairy", "nut-free", "lactose", "allerg",
        "without meat", "no meat", "sugar-free", "low calorie",
        "healthy", "keto", "paleo",
    ],
    "dish_price":         [
        "price", "cost", "how much", "expensive", "cheap",
        "affordable", "what does it cost",
    ],
    "menu_lookup":        [
        "available", "availability", "do you have", "menu",
        "show menu", "full menu", "what do you serve", "what can i order",
        "what food", "what dishes",
    ],
    "categories":         [
        "category", "categories", "types of food", "sections",
        "what kind of food",
    ],
    "user_orders":        [
        "my order", "my orders", "order status", "recent orders",
        "my recent order", "what did i order", "order history",
    ],
    "order_tracking":     [
        "track", "where is my order", "order #", "order number",
        "how long", "when will", "is my order ready", "eta",
        "status of order",
    ],
    "order_stats":        [
        "sales", "total orders", "order stats", "statistics",
        "analytics", "revenue", "performance", "how many orders",
    ],
    "specials":           [
        "special", "deal", "offer", "discount", "promo",
        "promotion", "today's special", "happy hour", "combo",
        "limited time",
    ],
    "recommendations":    [
        "recommend", "suggestion", "what should i order",
        "surprise me", "what's good", "what do you suggest",
        "help me choose", "best for me", "what would you recommend",
    ],
    "restaurant_info":    [
        "open", "opening hours", "hours", "close", "closing",
        "address", "location", "where are you", "contact",
        "phone", "email", "wifi", "parking", "about",
        "tell me about", "how to get", "directions",
    ],
    "table_availability": [
        "reserve", "book", "reservation", "seat", "table for",
        "available table", "book a table", "make a reservation",
        "capacity",
    ],
    "feedback":           [
        "complaint", "feedback", "review", "bad experience",
        "rate", "rating", "not happy", "problem", "issue",
        "wrong order", "cold food", "rude staff", "complain",
    ],
    "payment":            [
        "pay", "payment", "cash", "card", "credit card",
        "debit card", "online payment", "split bill",
        "bill", "invoice", "receipt", "tip",
    ],
    "delivery":           [
        "deliver", "delivery", "takeaway", "take away",
        "takeout", "take out", "home delivery", "order online",
        "delivery time", "delivery fee", "delivery area",
        "can you deliver",
    ],
    "catering":           [
        "cater", "catering", "event", "party", "bulk order",
        "large order", "corporate", "wedding", "birthday",
    ],
    "nutrition":          [
        "calorie", "calories", "nutrition", "nutritional",
        "protein", "carb", "fat", "sodium", "fiber",
        "macro", "healthy option",
    ],
}


# ============================================================
# Small helpers
# ============================================================

def money(value) -> str:
    if value is None:
        return "0.00"
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    return str(value)


def normalize(text: str) -> str:
    return (text or "").strip().lower()


def contains_any(text: str, words: List[str]) -> bool:
    text = normalize(text)
    return any(word in text for word in words)


def extract_keywords(message: str) -> List[str]:
    cleaned = (
        normalize(message)
        .replace(",", " ").replace(".", " ").replace("?", " ")
        .replace("!", " ").replace("-", " ").replace("'", " ")
    )
    words = [w.strip() for w in cleaned.split() if len(w.strip()) >= 3]
    return list(dict.fromkeys(words))


def detect_intent(message: str) -> str:
    text = normalize(message)
    for intent, keywords in INTENT_MAP.items():
        if contains_any(text, keywords):
            return intent
    return "general_lookup"


# ============================================================
# Menu queries
# ============================================================

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
        query |= Q(tags__name__icontains=word)       # dietary tags

    return (
        MenuItem.objects.select_related("category")
        .prefetch_related("tags")
        .filter(query)
        .distinct()
    )


def get_available_menu_items(limit: int = 20) -> List[Dict]:
    items = (
        MenuItem.objects.select_related("category")
        .prefetch_related("tags")
        .filter(availability=True)
        .order_by("category__name", "name")[:limit]
    )
    return [_serialize_item(item) for item in items]


def get_menu_item_details(message: str) -> List[Dict]:
    items = find_matching_menu_items(message)[:10]
    return [_serialize_item(item, include_availability=True) for item in items]


def get_menu_categories() -> List[str]:
    return list(MenuCategory.objects.order_by("name").values_list("name", flat=True))


def _serialize_item(item, include_availability: bool = False) -> Dict:
    data = {
        "name": item.name,
        "category": item.category.name,
        "price": money(item.price),
        "description": item.description or "N/A",
        "ingredients": item.ingredients or "N/A",
        "tags": [t.name for t in item.tags.all()] if hasattr(item, "tags") else [],
    }
    if hasattr(item, "calories") and item.calories:
        data["calories"] = item.calories
    if hasattr(item, "spice_level") and item.spice_level:
        data["spice_level"] = item.spice_level
    if include_availability:
        data["available"] = item.availability
    return data


# ============================================================
# Dietary filtering
# ============================================================

def get_items_by_dietary_preference(message: str) -> List[Dict]:
    """
    Filter menu items by dietary tag or ingredient exclusion
    derived from the user message.
    """
    dietary_map = {
        "vegan":       ["vegan"],
        "vegetarian":  ["vegetarian", "veg"],
        "gluten":      ["gluten-free", "gluten free"],
        "halal":       ["halal"],
        "kosher":      ["kosher"],
        "dairy":       ["dairy-free", "no dairy", "lactose-free"],
        "nut":         ["nut-free", "no nuts"],
        "sugar":       ["sugar-free"],
        "keto":        ["keto", "low-carb"],
        "paleo":       ["paleo"],
        "spicy":       ["spicy", "hot"],
        "healthy":     ["healthy", "low calorie", "light"],
    }

    text = normalize(message)
    filters = Q(availability=True)
    matched = False

    for keyword, tags in dietary_map.items():
        if keyword in text:
            matched = True
            tag_q = Q()
            for tag in tags:
                tag_q |= Q(tags__name__icontains=tag)
                tag_q |= Q(description__icontains=tag)
                tag_q |= Q(ingredients__icontains=tag)
            filters &= tag_q

    if not matched:
        return []

    items = (
        MenuItem.objects.select_related("category")
        .prefetch_related("tags")
        .filter(filters)
        .distinct()[:15]
    )
    return [_serialize_item(item) for item in items]


# ============================================================
# Nutrition
# ============================================================

def get_nutrition_info(message: str) -> List[Dict]:
    items = find_matching_menu_items(message)[:5]
    result = []
    for item in items:
        entry = {
            "name": item.name,
            "price": money(item.price),
            "ingredients": item.ingredients or "N/A",
        }
        for field in ["calories", "protein_g", "carbs_g", "fat_g", "sodium_mg", "fiber_g"]:
            val = getattr(item, field, None)
            if val is not None:
                entry[field] = val
        result.append(entry)
    return result


# ============================================================
# Analytics
# ============================================================

def get_most_ordered_dishes(limit: int = 5) -> List[Dict]:
    rows = (
        OrderItem.objects
        .values("menu_item__id", "menu_item__name")
        .annotate(order_count=Count("id"))
        .order_by("-order_count")[:limit]
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
    total_orders    = Order.objects.count()
    completed       = Order.objects.filter(status="completed").count()
    pending         = Order.objects.filter(status="pending").count()
    preparing       = Order.objects.filter(status="preparing").count()
    served          = Order.objects.filter(status="served").count()
    cancelled       = Order.objects.filter(status="cancelled").count()

    total_sales = (
        Order.objects.filter(status="completed")
        .aggregate(total=Sum("total_amount"))
        .get("total") or Decimal("0.00")
    )
    avg_feedback = Feedback.objects.aggregate(avg=Avg("rating")).get("avg")

    return {
        "total_orders":             total_orders,
        "completed_orders":         completed,
        "pending_orders":           pending,
        "preparing_orders":         preparing,
        "served_orders":            served,
        "cancelled_orders":         cancelled,
        "total_sales":              money(total_sales),
        "average_feedback_rating":  round(avg_feedback, 2) if avg_feedback else None,
    }


# ============================================================
# Customer-specific queries
# ============================================================

def get_user_recent_orders(user, limit: int = 5) -> List[Dict]:
    if not user or not user.is_authenticated:
        return []

    orders = (
        Order.objects.select_related("table")
        .prefetch_related("items__menu_item")
        .filter(user=user)
        .order_by("-created_at")[:limit]
    )

    data = []
    for order in orders:
        items = [
            {
                "name": item.menu_item.name,
                "quantity": item.quantity,
                "line_total": money(item.price),
            }
            for item in order.items.all()
        ]
        data.append({
            "order_id":      order.id,
            "status":        order.status,
            "total_amount":  money(order.total_amount),
            "table_id":      order.table.id if order.table else None,
            "special_notes": order.special_notes or "",
            "created_at":    str(order.created_at),
            "items":         items,
        })
    return data


def get_order_by_id(order_id: int, user) -> Dict:
    """Live order tracking by ID."""
    try:
        order = (
            Order.objects.select_related("table")
            .prefetch_related("items__menu_item")
            .get(id=order_id, user=user)
        )
        STATUS_NEXT = {
            "pending":    "Your order has been received and is waiting to be confirmed.",
            "preparing":  "Our kitchen is preparing your order right now.",
            "served":     "Your order has been served. Enjoy your meal!",
            "completed":  "Your order is complete. Thank you for dining with us!",
            "cancelled":  "This order has been cancelled. Please contact staff if this is unexpected.",
        }
        return {
            "order_id":      order.id,
            "status":        order.status,
            "status_message": STATUS_NEXT.get(order.status, "Status unknown."),
            "placed_at":     str(order.created_at),
            "estimated_ready": str(getattr(order, "estimated_ready_at", "N/A")),
            "table":         order.table.id if order.table else "N/A",
            "items": [
                {"name": i.menu_item.name, "qty": i.quantity}
                for i in order.items.all()
            ],
            "total": money(order.total_amount),
        }
    except Order.DoesNotExist:
        return {"error": "Order not found. Please check the order number."}


def get_user_feedback_history(user) -> List[Dict]:
    if not user or not user.is_authenticated:
        return []
    return list(
        Feedback.objects.filter(order__user=user)
        .order_by("-created_at")[:5]
        .values("rating", "comment", "created_at")
    )


# ============================================================
# Personalized recommendations
# ============================================================

def get_personalized_recommendations(user, limit: int = 5) -> List[Dict]:
    """
    Suggest popular dishes the user hasn't tried yet.
    Falls back to overall most-ordered if user is not authenticated.
    """
    if not user or not user.is_authenticated:
        return get_most_ordered_dishes(limit)

    already_tried = (
        OrderItem.objects.filter(order__user=user)
        .values_list("menu_item_id", flat=True)
        .distinct()
    )

    rows = (
        OrderItem.objects
        .exclude(menu_item_id__in=already_tried)
        .filter(menu_item__availability=True)
        .values("menu_item__id", "menu_item__name")
        .annotate(order_count=Count("id"))
        .order_by("-order_count")[:limit]
    )

    if not rows:
        return get_most_ordered_dishes(limit)

    ids = [r["menu_item__id"] for r in rows]
    items = MenuItem.objects.filter(id__in=ids).select_related("category")
    item_map = {i.id: i for i in items}

    return [
        {
            "name": item_map[r["menu_item__id"]].name,
            "category": item_map[r["menu_item__id"]].category.name,
            "price": money(item_map[r["menu_item__id"]].price),
            "times_ordered": r["order_count"],
            "reason": "Popular with other customers and you haven't tried it yet!",
        }
        for r in rows
        if r["menu_item__id"] in item_map
    ]


# ============================================================
# Specials & promotions
# ============================================================

def get_todays_specials() -> List[Dict]:
    from django.utils import timezone

    today = timezone.now().weekday()   # 0 = Monday … 6 = Sunday

    # Requires a `special_day` IntegerField (0–6) or similar on MenuItem
    qs = MenuItem.objects.filter(availability=True)
    if hasattr(MenuItem, "special_day"):
        qs = qs.filter(special_day=today)
    elif hasattr(MenuItem, "is_daily_special"):
        qs = qs.filter(is_daily_special=True)
    else:
        return []   # model doesn't support specials yet

    return list(qs.select_related("category").values(
        "name", "price", "description", "category__name"
    )[:10])


def get_active_promotions() -> List[Dict]:
    from django.utils import timezone

    try:
        from promotions.models import Promotion
    except ImportError:
        return []   # promotions app not installed

    now = timezone.now()
    promos = Promotion.objects.filter(
        start_date__lte=now,
        end_date__gte=now,
        is_active=True,
    ).values("title", "description", "discount_percent", "applies_to", "end_date")

    return [
        {**p, "end_date": str(p["end_date"])}
        for p in promos
    ]


# ============================================================
# Table availability
# ============================================================

def get_table_availability() -> Dict:
    try:
        from tables.models import Table
    except ImportError:
        return {"error": "Table management module not available."}

    tables = Table.objects.all()
    return {
        "total_tables":     tables.count(),
        "available":        tables.filter(status="available").count(),
        "occupied":         tables.filter(status="occupied").count(),
        "reserved":         tables.filter(status="reserved").count(),
        "available_sizes":  list(
            tables.filter(status="available")
            .values_list("capacity", flat=True)
            .order_by("capacity")
        ),
    }


# ============================================================
# Restaurant info  (configure in settings.py)
# ============================================================

def get_restaurant_info() -> Dict:
    return {
        "name":                  getattr(settings, "RESTAURANT_NAME",    "Our Restaurant"),
        "address":               getattr(settings, "RESTAURANT_ADDRESS", "N/A"),
        "phone":                 getattr(settings, "RESTAURANT_PHONE",   "N/A"),
        "email":                 getattr(settings, "RESTAURANT_EMAIL",   "N/A"),
        "opening_hours":         getattr(settings, "RESTAURANT_HOURS",   {}),
        "cuisine_type":          getattr(settings, "RESTAURANT_CUISINE", "N/A"),
        "wifi_available":        getattr(settings, "RESTAURANT_WIFI",    False),
        "parking_available":     getattr(settings, "RESTAURANT_PARKING", False),
        "accepts_reservations":  getattr(settings, "RESTAURANT_RESERVATIONS", True),
        "delivery_available":    getattr(settings, "RESTAURANT_DELIVERY", False),
        "takeaway_available":    getattr(settings, "RESTAURANT_TAKEAWAY", False),
    }


# ============================================================
# Payment info
# ============================================================

def get_payment_info() -> Dict:
    return {
        "accepted_methods":   getattr(settings, "PAYMENT_METHODS",      ["Cash", "Credit Card", "Debit Card"]),
        "online_payment":     getattr(settings, "PAYMENT_ONLINE",       False),
        "split_bill":         getattr(settings, "PAYMENT_SPLIT_BILL",   True),
        "service_charge":     getattr(settings, "PAYMENT_SERVICE_CHARGE", "10%"),
        "tip_guidance":       getattr(settings, "PAYMENT_TIP_GUIDANCE", "Tips are appreciated but not mandatory."),
    }


# ============================================================
# Delivery info
# ============================================================

def get_delivery_info() -> Dict:
    return {
        "delivery_available":   getattr(settings, "RESTAURANT_DELIVERY",      False),
        "delivery_radius_km":   getattr(settings, "DELIVERY_RADIUS_KM",       5),
        "delivery_fee":         getattr(settings, "DELIVERY_FEE",             "2.99"),
        "min_order_amount":     getattr(settings, "DELIVERY_MIN_ORDER",       "15.00"),
        "estimated_time_mins":  getattr(settings, "DELIVERY_ESTIMATED_MINS",  45),
        "platforms":            getattr(settings, "DELIVERY_PLATFORMS",       []),
    }


# ============================================================
# Catering info
# ============================================================

def get_catering_info() -> Dict:
    return {
        "catering_available": getattr(settings, "CATERING_AVAILABLE", False),
        "min_guests":         getattr(settings, "CATERING_MIN_GUESTS", 20),
        "advance_notice_days":getattr(settings, "CATERING_NOTICE_DAYS", 3),
        "contact":            getattr(settings, "CATERING_CONTACT",    getattr(settings, "RESTAURANT_EMAIL", "N/A")),
        "packages":           getattr(settings, "CATERING_PACKAGES",   []),
    }


# ============================================================
# Extract order ID from message
# ============================================================

def extract_order_id(message: str) -> Optional[int]:
    import re
    match = re.search(r"\b(?:order[#\s]*)?(\d{1,6})\b", normalize(message))
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


# ============================================================
# Structured context builder
# ============================================================

def build_structured_context(user, message: str) -> Dict:
    intent = detect_intent(message)

    # --- popular dishes ---
    if intent == "popular_dishes":
        return {"intent": intent, "data": {
            "most_ordered_dishes": get_most_ordered_dishes(),
        }}

    # --- top rated ---
    if intent == "top_rated_dishes":
        return {"intent": intent, "data": {
            "top_rated_dishes": get_top_rated_dishes(),
        }}

    # --- dietary ---
    if intent == "dietary":
        items = get_items_by_dietary_preference(message)
        if items:
            return {"intent": intent, "data": {"dietary_items": items}}
        return {"intent": intent, "data": {
            "message": "No specific dietary items found. Showing full menu.",
            "available_menu_items": get_available_menu_items(),
        }}

    # --- nutrition ---
    if intent == "nutrition":
        nutrition = get_nutrition_info(message)
        if nutrition:
            return {"intent": intent, "data": {"nutrition_info": nutrition}}
        return {"intent": intent, "data": {
            "message": "Nutritional information not available for those items.",
        }}

    # --- dish contents / price / menu lookup / general ---
    if intent in {"dish_contents", "dish_price", "menu_lookup", "general_lookup"}:
        matched = get_menu_item_details(message)
        if matched:
            return {"intent": intent, "data": {"matched_menu_items": matched}}
        return {"intent": intent, "data": {
            "available_menu_items": get_available_menu_items(),
        }}

    # --- categories ---
    if intent == "categories":
        return {"intent": intent, "data": {
            "categories": get_menu_categories(),
        }}

    # --- user order history ---
    if intent == "user_orders":
        return {"intent": intent, "data": {
            "user_recent_orders": get_user_recent_orders(user),
        }}

    # --- order tracking by ID ---
    if intent == "order_tracking":
        order_id = extract_order_id(message)
        if order_id:
            return {"intent": intent, "data": {
                "order_details": get_order_by_id(order_id, user),
            }}
        # No ID found — show recent orders
        return {"intent": intent, "data": {
            "message": "No order number detected. Showing your recent orders.",
            "user_recent_orders": get_user_recent_orders(user),
        }}

    # --- order analytics ---
    if intent == "order_stats":
        return {"intent": intent, "data": {
            "order_stats":         get_order_stats(),
            "most_ordered_dishes": get_most_ordered_dishes(),
            "top_rated_dishes":    get_top_rated_dishes(),
        }}

    # --- specials & promotions ---
    if intent == "specials":
        return {"intent": intent, "data": {
            "todays_specials":   get_todays_specials(),
            "active_promotions": get_active_promotions(),
        }}

    # --- recommendations ---
    if intent == "recommendations":
        return {"intent": intent, "data": {
            "recommended_dishes": get_personalized_recommendations(user),
            "top_rated_dishes":   get_top_rated_dishes(3),
        }}

    # --- restaurant info ---
    if intent == "restaurant_info":
        return {"intent": intent, "data": {
            "restaurant_info": get_restaurant_info(),
        }}

    # --- table availability ---
    if intent == "table_availability":
        return {"intent": intent, "data": {
            "table_availability": get_table_availability(),
            "restaurant_info":    {
                "accepts_reservations": get_restaurant_info()["accepts_reservations"],
                "phone": get_restaurant_info()["phone"],
            },
        }}

    # --- feedback / complaints ---
    if intent == "feedback":
        return {"intent": intent, "data": {
            "user_feedback_history": get_user_feedback_history(user),
            "contact": {
                "phone": get_restaurant_info()["phone"],
                "email": get_restaurant_info()["email"],
            },
        }}

    # --- payment ---
    if intent == "payment":
        return {"intent": intent, "data": {
            "payment_info": get_payment_info(),
        }}

    # --- delivery ---
    if intent == "delivery":
        return {"intent": intent, "data": {
            "delivery_info": get_delivery_info(),
        }}

    # --- catering ---
    if intent == "catering":
        return {"intent": intent, "data": {
            "catering_info": get_catering_info(),
        }}

    # --- fallback ---
    return {"intent": "fallback", "data": {
        "available_menu_items":  get_available_menu_items(),
        "most_ordered_dishes":   get_most_ordered_dishes(3),
        "restaurant_info":       get_restaurant_info(),
    }}


# ============================================================
# OpenAI system prompt
# ============================================================

def system_prompt() -> str:
    return (
        "You are a smart, friendly, and professional restaurant assistant.\n\n"
        "STRICT RULES:\n"
        "1. Answer ONLY from the structured database facts provided to you.\n"
        "   Never invent dishes, prices, ingredients, ratings, or order details.\n"
        "2. If information is missing or unavailable, say so clearly and politely.\n"
        "3. Keep answers concise (2-4 sentences) unless listing items.\n"
        "4. Format prices as $X.XX.\n"
        "5. For lists of dishes, use clean bullet-point format with name and price.\n"
        "6. For dietary questions, mention allergen info if present in the data.\n"
        "7. For order tracking, always state current status AND what happens next.\n"
        "8. For recommendations, briefly explain why you suggest each dish.\n"
        "9. If a user seems frustrated or is complaining, respond with empathy first,\n"
        "   then offer the relevant information or contact details.\n"
        "10. Never expose internal field names, IDs, or raw database structures.\n"
        "11. For reservation requests, provide availability and contact details.\n"
        "12. For delivery queries, state clearly if delivery is available and the details.\n"
        "13. For catering, always direct the user to contact the restaurant directly.\n"
        "14. Be warm, welcoming, and make the customer feel valued."
    )


# ============================================================
# Main entry point
# ============================================================

def ask_chatbot(user, message: str) -> str:
    context = build_structured_context(user, message)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": system_prompt(),
            },
            {
                "role": "system",
                "content": f"STRUCTURED DATABASE FACTS (answer only from this):\n{context}",
            },
            {
                "role": "user",
                "content": message,
            },
        ],
        temperature=0.4,       # slightly creative but mostly factual
        max_tokens=600,
    )

    return response.choices[0].message.content.strip()