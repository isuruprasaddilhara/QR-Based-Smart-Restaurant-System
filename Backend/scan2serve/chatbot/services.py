from decimal import Decimal
from typing import Dict, List, Optional

from django.conf import settings
from django.db.models import Avg, Count, Max, Min, Q, Sum
from openai import OpenAI

from menu.models import MenuItem, MenuCategory
from orders.models import Order, OrderItem, Feedback

client = OpenAI(api_key=settings.OPENAI_API_KEY)


# ----------------------------
# Small helpers
# ----------------------------

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
    STOPWORDS = {
        "the", "and", "for", "are", "you", "that", "this", "with",
        "have", "from", "can", "what", "which", "how", "does", "any",
        "your", "our", "its", "not", "but", "also", "has", "get",
        "will", "please", "want", "need", "like", "tell", "show",
        "give", "make", "dish", "food", "meal", "item", "items",
    }
    cleaned = (
        normalize(message)
        .replace(",", " ").replace(".", " ").replace("?", " ")
        .replace("!", " ").replace("-", " ").replace("'", " ")
        .replace("(", " ").replace(")", " ")
    )
    words = [
        w.strip() for w in cleaned.split()
        if len(w.strip()) >= 3 and w.strip() not in STOPWORDS
    ]
    return list(dict.fromkeys(words))


def parse_budget(message: str) -> Optional[float]:
    """Extract a budget figure from a message like 'under $20' or 'less than 500'."""
    import re
    patterns = [
        r"under\s*\$?\s*(\d+(?:\.\d+)?)",
        r"less\s+than\s*\$?\s*(\d+(?:\.\d+)?)",
        r"below\s*\$?\s*(\d+(?:\.\d+)?)",
        r"cheaper\s+than\s*\$?\s*(\d+(?:\.\d+)?)",
        r"within\s*\$?\s*(\d+(?:\.\d+)?)",
        r"budget\s+of\s*\$?\s*(\d+(?:\.\d+)?)",
        r"\$\s*(\d+(?:\.\d+)?)",
    ]
    text = normalize(message)
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))
    return None


# ----------------------------
# Menu queries
# ----------------------------

def find_matching_menu_items(message: str, available_only: bool = False):
    keywords = extract_keywords(message)
    if not keywords:
        return MenuItem.objects.none()

    query = Q()
    for word in keywords:
        query |= Q(name__icontains=word)
        query |= Q(description__icontains=word)
        query |= Q(ingredients__icontains=word)
        query |= Q(category__name__icontains=word)
        query |= Q(tags__icontains=word)  # if you have a tags field

    qs = MenuItem.objects.select_related("category").filter(query).distinct()
    if available_only:
        qs = qs.filter(availability=True)
    return qs


def get_available_menu_items(limit: int = 20) -> List[Dict]:
    items = (
        MenuItem.objects.select_related("category")
        .filter(availability=True)
        .order_by("category__name", "name")[:limit]
    )
    return [_format_menu_item(item) for item in items]


def get_full_menu() -> Dict[str, List[Dict]]:
    """Return the full menu grouped by category."""
    items = (
        MenuItem.objects.select_related("category")
        .filter(availability=True)
        .order_by("category__name", "name")
    )
    menu: Dict[str, List] = {}
    for item in items:
        cat = item.category.name
        menu.setdefault(cat, [])
        menu[cat].append(_format_menu_item(item))
    return menu


def get_menu_item_details(message: str, available_only: bool = False) -> List[Dict]:
    items = find_matching_menu_items(message, available_only=available_only)[:10]
    return [_format_menu_item_full(item) for item in items]


def get_menu_categories() -> List[Dict]:
    cats = MenuCategory.objects.order_by("name")
    result = []
    for cat in cats:
        count = MenuItem.objects.filter(category=cat, availability=True).count()
        result.append({"name": cat.name, "available_items": count})
    return result


def get_items_by_category(message: str) -> List[Dict]:
    categories = MenuCategory.objects.all()
    text = normalize(message)
    matched_cat = None
    for cat in categories:
        if normalize(cat.name) in text or text in normalize(cat.name):
            matched_cat = cat
            break

    if not matched_cat:
        # Try keyword match on category name
        keywords = extract_keywords(message)
        for keyword in keywords:
            try:
                matched_cat = categories.filter(name__icontains=keyword).first()
                if matched_cat:
                    break
            except Exception:
                pass

    if matched_cat:
        items = (
            MenuItem.objects.select_related("category")
            .filter(category=matched_cat, availability=True)
            .order_by("name")
        )
        return [_format_menu_item_full(item) for item in items]
    return []


def get_items_by_budget(max_price: float) -> List[Dict]:
    items = (
        MenuItem.objects.select_related("category")
        .filter(availability=True, price__lte=max_price)
        .order_by("price")[:15]
    )
    return [_format_menu_item(item) for item in items]


def get_price_range() -> Dict:
    result = MenuItem.objects.filter(availability=True).aggregate(
        min_price=Min("price"),
        max_price=Max("price"),
        avg_price=Avg("price"),
    )
    return {
        "min_price": money(result["min_price"]),
        "max_price": money(result["max_price"]),
        "avg_price": money(result["avg_price"]),
    }


def get_dietary_items(dietary_type: str) -> List[Dict]:
    """
    Filter by dietary preference based on name/description/ingredients/tags.
    dietary_type: 'vegetarian', 'vegan', 'gluten_free', 'dairy_free',
                  'spicy', 'non_spicy', 'halal', 'low_calorie', etc.
    """
    DIETARY_KEYWORDS = {
        "vegetarian": ["vegetarian", "veggie", "no meat", "plant"],
        "vegan": ["vegan", "plant-based", "no dairy", "no eggs"],
        "gluten_free": ["gluten-free", "gluten free", "no gluten", "gf"],
        "dairy_free": ["dairy-free", "dairy free", "no dairy", "lactose"],
        "spicy": ["spicy", "hot", "chili", "jalapeño", "sriracha", "pepper"],
        "non_spicy": ["mild", "non-spicy", "not spicy", "no spice"],
        "halal": ["halal"],
        "low_calorie": ["light", "low calorie", "healthy", "diet", "salad", "grilled"],
        "seafood": ["fish", "seafood", "prawn", "shrimp", "crab", "lobster", "salmon"],
        "chicken": ["chicken", "poultry"],
        "beef": ["beef", "steak", "burger"],
        "lamb": ["lamb", "mutton"],
        "dessert": ["dessert", "sweet", "cake", "ice cream", "pudding"],
    }

    keywords = DIETARY_KEYWORDS.get(dietary_type, [dietary_type.replace("_", " ")])
    query = Q()
    for kw in keywords:
        query |= Q(name__icontains=kw)
        query |= Q(description__icontains=kw)
        query |= Q(ingredients__icontains=kw)
        # query |= Q(tags__icontains=kw)  # uncomment if tags field exists

    items = (
        MenuItem.objects.select_related("category")
        .filter(query, availability=True)
        .distinct()[:15]
    )
    return [_format_menu_item_full(item) for item in items]


def _format_menu_item(item) -> Dict:
    return {
        "name": item.name,
        "category": item.category.name,
        "price": money(item.price),
        "description": item.description or "N/A",
    }


def _format_menu_item_full(item) -> Dict:
    return {
        "name": item.name,
        "category": item.category.name,
        "price": money(item.price),
        "available": item.availability,
        "ingredients": item.ingredients or "N/A",
        "description": item.description or "N/A",
    }


# ----------------------------
# Analytics / recommendations
# ----------------------------

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
            review_count=Count("orderitem__order__feedback", distinct=True),
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
            "category": item.category.name,
            "description": item.description or "",
        }
        for item in rows
    ]


def get_chef_recommendations() -> List[Dict]:
    """Best combo: highly rated + frequently ordered."""
    top_rated_ids = set(
        MenuItem.objects
        .filter(orderitem__order__feedback__isnull=False)
        .annotate(avg_rating=Avg("orderitem__order__feedback__rating"))
        .filter(avg_rating__gte=4.0)
        .values_list("id", flat=True)
    )
    top_ordered_ids = set(
        OrderItem.objects
        .values("menu_item__id")
        .annotate(cnt=Count("id"))
        .order_by("-cnt")[:20]
        .values_list("menu_item__id", flat=True)
    )
    chef_picks_ids = top_rated_ids & top_ordered_ids

    items = (
        MenuItem.objects.select_related("category")
        .filter(id__in=chef_picks_ids, availability=True)[:6]
    )
    if not items:
        # Fall back to top rated
        return get_top_rated_dishes(limit=5)
    return [_format_menu_item_full(item) for item in items]


def get_new_or_featured_items() -> List[Dict]:
    """Most recently added items (assumes created_at field on MenuItem)."""
    try:
        items = (
            MenuItem.objects.select_related("category")
            .filter(availability=True)
            .order_by("-created_at")[:5]
        )
        return [_format_menu_item_full(item) for item in items]
    except Exception:
        return get_available_menu_items(limit=5)


def get_similar_items(message: str) -> List[Dict]:
    """Find items similar to what user described."""
    matched = find_matching_menu_items(message, available_only=True)[:5]
    if matched:
        categories = list(set(item.category_id for item in matched))
        related = (
            MenuItem.objects.select_related("category")
            .filter(category_id__in=categories, availability=True)
            .exclude(id__in=[item.id for item in matched])
            .order_by("?")[:5]  # random similar
        )
        return [_format_menu_item_full(item) for item in matched] + \
               [_format_menu_item(item) for item in related]
    return get_available_menu_items(limit=10)


def get_combo_suggestions() -> List[Dict]:
    """Suggest starter + main + dessert combos based on popular items."""
    combos = []
    for cat_keyword in [["starter", "appetizer", "soup"], ["main", "entrée", "rice", "pasta"], ["dessert", "sweet"]]:
        query = Q()
        for kw in cat_keyword:
            query |= Q(category__name__icontains=kw)
        item = (
            MenuItem.objects.select_related("category")
            .filter(query, availability=True)
            .order_by("?")
            .first()
        )
        if item:
            combos.append(_format_menu_item(item))
    return combos


# ----------------------------
# Order & feedback queries
# ----------------------------

def get_order_stats() -> Dict:
    total_orders = Order.objects.count()
    completed_orders = Order.objects.filter(status="completed").count()
    pending_orders = Order.objects.filter(status="pending").count()
    preparing_orders = Order.objects.filter(status="preparing").count()
    served_orders = Order.objects.filter(status="served").count()

    total_sales = (
        Order.objects.filter(status="completed")
        .aggregate(total=Sum("total_amount"))
        .get("total") or Decimal("0.00")
    )
    avg_feedback = Feedback.objects.aggregate(avg=Avg("rating")).get("avg")

    return {
        "total_orders": total_orders,
        "completed_orders": completed_orders,
        "pending_orders": pending_orders,
        "preparing_orders": preparing_orders,
        "served_orders": served_orders,
        "total_sales": money(total_sales),
        "average_feedback_rating": round(avg_feedback, 2) if avg_feedback is not None else None,
    }


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
            "order_id": order.id,
            "status": order.status,
            "total_amount": money(order.total_amount),
            "table_id": order.table.id if order.table else None,
            "special_notes": order.special_notes or "",
            "created_at": str(order.created_at),
            "items": items,
        })
    return data


def get_user_favorite_items(user, limit: int = 5) -> List[Dict]:
    """Items this user has ordered most frequently."""
    if not user or not user.is_authenticated:
        return []

    rows = (
        OrderItem.objects
        .filter(order__user=user)
        .values("menu_item__id", "menu_item__name")
        .annotate(times_ordered=Count("id"))
        .order_by("-times_ordered")[:limit]
    )
    result = []
    for row in rows:
        try:
            item = MenuItem.objects.select_related("category").get(id=row["menu_item__id"])
            result.append({
                **_format_menu_item(item),
                "times_ordered": row["times_ordered"],
            })
        except MenuItem.DoesNotExist:
            pass
    return result


def get_user_feedback_history(user, limit: int = 5) -> List[Dict]:
    if not user or not user.is_authenticated:
        return []

    feedbacks = (
        Feedback.objects
        .select_related("order")
        .filter(order__user=user)
        .order_by("-created_at")[:limit]
    )
    return [
        {
            "order_id": fb.order.id,
            "rating": fb.rating,
            "comment": fb.comment or "",
            "created_at": str(fb.created_at),
        }
        for fb in feedbacks
    ]


def get_recent_feedbacks(limit: int = 5) -> List[Dict]:
    feedbacks = (
        Feedback.objects
        .select_related("order")
        .order_by("-created_at")[:limit]
    )
    return [
        {
            "rating": fb.rating,
            "comment": fb.comment or "",
            "created_at": str(fb.created_at),
        }
        for fb in feedbacks
    ]


# ----------------------------
# Intent detection
# ----------------------------

# Each intent maps to a list of trigger phrases.
INTENT_PATTERNS = {
    "popular_dishes": [
        "most ordered", "popular dish", "popular dishes", "best selling",
        "top selling", "most popular", "trending", "people love", "everyone orders",
        "what do people order", "crowd favorite", "crowd favourite",
    ],
    "top_rated_dishes": [
        "top rated", "best rated", "highest rated", "best dish", "best dishes",
        "most loved", "highest rating", "best reviews", "best reviewed",
    ],
    "chef_recommendation": [
        "recommend", "recommendation", "suggestions", "suggest", "what should i order",
        "what do you suggest", "chef", "house special", "speciality", "specialty",
        "what's good", "whats good", "what is good", "what's best", "whats best",
        "must try", "must-try", "must have", "must-have", "best pick", "top pick",
        "what to order", "help me choose", "help me decide", "what would you recommend",
        "surprise me", "your pick", "your choice", "staff pick",
    ],
    "new_items": [
        "new dish", "new dishes", "new item", "new items", "new on menu", "new arrival",
        "latest dish", "recently added", "what's new", "whats new", "featured",
    ],
    "combo_suggestion": [
        "combo", "set meal", "meal deal", "starter and main", "full meal",
        "what goes with", "pair with", "combination", "package",
    ],
    "dietary_vegetarian": [
        "vegetarian", "veggie", "no meat", "meatless", "plant based", "plant-based",
    ],
    "dietary_vegan": [
        "vegan", "no animal", "plant only", "no dairy no eggs",
    ],
    "dietary_gluten_free": [
        "gluten free", "gluten-free", "no gluten", "celiac", "coeliac",
    ],
    "dietary_spicy": [
        "spicy", "hot dish", "spicy food", "spicy option", "spicy menu",
        "something spicy", "hot and spicy",
    ],
    "dietary_non_spicy": [
        "not spicy", "non spicy", "mild", "no spice", "bland", "without spice",
    ],
    "dietary_halal": [
        "halal", "halal food", "halal option",
    ],
    "dietary_seafood": [
        "seafood", "fish", "prawn", "shrimp", "crab", "lobster",
    ],
    "dietary_chicken": [
        "chicken", "poultry", "grilled chicken", "fried chicken",
    ],
    "dietary_beef": [
        "beef", "steak", "burger", "beef dish",
    ],
    "dietary_dessert": [
        "dessert", "sweet", "something sweet", "pudding", "cake", "ice cream",
    ],
    "budget_search": [
        "under", "less than", "below", "cheap", "cheapest", "affordable",
        "budget", "inexpensive", "low price", "low cost", "economy",
    ],
    "price_range": [
        "price range", "how expensive", "how cheap", "minimum price", "maximum price",
        "cheapest dish", "most expensive", "price list", "pricing",
    ],
    "dish_contents": [
        "ingredient", "ingredients", "what is in", "contains", "content of",
        "what's inside", "whats inside", "made of", "made with", "what does it contain",
        "allergen", "allergy",
    ],
    "dish_price": [
        "price", "cost", "how much", "how much is", "how much does",
    ],
    "menu_lookup": [
        "show menu", "full menu", "see menu", "view menu", "entire menu",
        "whole menu", "complete menu", "all items", "all dishes", "what do you serve",
        "what do you have", "what's available", "whats available", "do you have",
        "is there", "menu please", "your menu",
    ],
    "categories": [
        "category", "categories", "type of food", "types of food",
        "sections", "section", "food type",
    ],
    "category_items": [
        # this is handled via contains_any for any category name dynamically
    ],
    "user_orders": [
        "my order", "my orders", "order status", "recent orders", "my recent order",
        "what did i order", "past order", "order history", "my history",
        "track my order", "where is my order",
    ],
    "user_favorites": [
        "my favorite", "my favourite", "what i usually order", "what i always order",
        "my go to", "my go-to", "i usually have", "i always have",
    ],
    "user_feedback": [
        "my feedback", "my review", "my rating", "my ratings", "my reviews",
    ],
    "order_stats": [
        "sales", "total orders", "order stats", "statistics", "analytics",
        "how many orders", "revenue", "total sales",
    ],
    "restaurant_info": [
        "about", "hours", "opening hours", "open", "close", "closing",
        "location", "address", "where are you", "contact", "phone",
        "reservation", "book a table", "booking", "table for", "wifi",
        "parking", "dress code", "pets allowed", "outdoor seating",
    ],
    "greeting": [
        "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
        "howdy", "greetings", "sup", "what's up",
    ],
    "thanks": [
        "thank", "thanks", "thank you", "cheers", "great", "awesome",
        "perfect", "wonderful", "brilliant",
    ],
    "help": [
        "help", "what can you do", "what can you help", "how do you work",
        "what are your features", "capabilities", "options",
    ],
    "feedback_general": [
        "reviews", "feedback", "ratings", "what do people think",
        "customer review", "customer feedback",
    ],
}


def detect_intent(message: str) -> str:
    text = normalize(message)

    for intent, phrases in INTENT_PATTERNS.items():
        if phrases and contains_any(text, phrases):
            return intent

    # Dynamic category match
    categories = MenuCategory.objects.values_list("name", flat=True)
    for cat in categories:
        if normalize(cat) in text:
            return "category_items"

    return "general_lookup"


# ----------------------------
# Structured context builder
# ----------------------------

def build_structured_context(user, message: str) -> Dict:
    intent = detect_intent(message)

    # --- Social / meta intents ---
    if intent == "greeting":
        return {
            "intent": intent,
            "data": {
                "message": "The user is greeting. Respond warmly and offer to help with the menu, recommendations, or their order.",
                "available_menu_items": get_available_menu_items(limit=5),
            }
        }

    if intent == "thanks":
        return {
            "intent": intent,
            "data": {
                "message": "The user is expressing thanks. Respond warmly.",
            }
        }

    if intent == "help":
        return {
            "intent": intent,
            "data": {
                "message": (
                    "Explain what you can help with: showing the full menu, "
                    "recommendations, popular/top-rated dishes, dietary options "
                    "(vegetarian, vegan, gluten-free, spicy, etc.), price info, "
                    "budget-based suggestions, order history, and general restaurant questions."
                ),
                "categories": get_menu_categories(),
            }
        }

    # --- Restaurant info ---
    if intent == "restaurant_info":
        return {
            "intent": intent,
            "data": {
                "message": (
                    "Answer based on any restaurant info you have. If the user asks "
                    "about hours, location, reservations, or policies and you don't "
                    "have that data, politely say you don't have that info and suggest "
                    "they contact the restaurant directly."
                ),
            }
        }

    # --- Popular / ratings ---
    if intent == "popular_dishes":
        return {
            "intent": intent,
            "data": {
                "most_ordered_dishes": get_most_ordered_dishes(),
            }
        }

    if intent == "top_rated_dishes":
        return {
            "intent": intent,
            "data": {
                "top_rated_dishes": get_top_rated_dishes(),
            }
        }

    if intent == "chef_recommendation":
        return {
            "intent": intent,
            "data": {
                "chef_recommendations": get_chef_recommendations(),
                "most_ordered_dishes": get_most_ordered_dishes(limit=3),
                "top_rated_dishes": get_top_rated_dishes(limit=3),
            }
        }

    if intent == "new_items":
        return {
            "intent": intent,
            "data": {
                "new_or_featured_items": get_new_or_featured_items(),
            }
        }

    if intent == "combo_suggestion":
        return {
            "intent": intent,
            "data": {
                "combo_suggestions": get_combo_suggestions(),
                "popular_dishes": get_most_ordered_dishes(limit=3),
            }
        }

    # --- Dietary filters ---
    dietary_map = {
        "dietary_vegetarian": "vegetarian",
        "dietary_vegan": "vegan",
        "dietary_gluten_free": "gluten_free",
        "dietary_spicy": "spicy",
        "dietary_non_spicy": "non_spicy",
        "dietary_halal": "halal",
        "dietary_seafood": "seafood",
        "dietary_chicken": "chicken",
        "dietary_beef": "beef",
        "dietary_dessert": "dessert",
    }
    if intent in dietary_map:
        dietary_type = dietary_map[intent]
        items = get_dietary_items(dietary_type)
        return {
            "intent": intent,
            "data": {
                "dietary_type": dietary_type,
                "matched_items": items if items else [],
                "note": "No items found for this dietary preference." if not items else "",
            }
        }

    # --- Budget ---
    if intent == "budget_search":
        budget = parse_budget(message)
        if budget:
            items = get_items_by_budget(budget)
            return {
                "intent": intent,
                "data": {
                    "budget": budget,
                    "items_within_budget": items,
                }
            }
        # No budget number found — fall through to price_range
        intent = "price_range"

    if intent == "price_range":
        return {
            "intent": intent,
            "data": {
                "price_range": get_price_range(),
                "cheapest_items": get_items_by_budget(999999)[:5],  # sorted by price asc
            }
        }

    # --- Dish info ---
    if intent in {"dish_contents", "dish_price"}:
        matched = get_menu_item_details(message)
        if matched:
            return {"intent": intent, "data": {"matched_menu_items": matched}}
        return {
            "intent": intent,
            "data": {
                "matched_menu_items": [],
                "available_menu_items": get_available_menu_items(limit=10),
            }
        }

    # --- Full menu / availability ---
    if intent == "menu_lookup":
        return {
            "intent": intent,
            "data": {
                "full_menu_by_category": get_full_menu(),
            }
        }

    if intent == "categories":
        return {
            "intent": intent,
            "data": {
                "categories": get_menu_categories(),
            }
        }

    if intent == "category_items":
        items = get_items_by_category(message)
        return {
            "intent": intent,
            "data": {
                "category_items": items if items else [],
                "note": "Could not identify a specific category. Showing available menu." if not items else "",
                "available_menu_items": get_available_menu_items(limit=5) if not items else [],
            }
        }

    # --- User-specific ---
    if intent == "user_orders":
        return {
            "intent": intent,
            "data": {
                "user_recent_orders": get_user_recent_orders(user),
            }
        }

    if intent == "user_favorites":
        return {
            "intent": intent,
            "data": {
                "user_favorite_items": get_user_favorite_items(user),
                "note": "Based on the user's order history.",
            }
        }

    if intent == "user_feedback":
        return {
            "intent": intent,
            "data": {
                "user_feedback_history": get_user_feedback_history(user),
            }
        }

    # --- Stats / analytics ---
    if intent == "order_stats":
        return {
            "intent": intent,
            "data": {
                "order_stats": get_order_stats(),
                "most_ordered_dishes": get_most_ordered_dishes(),
                "top_rated_dishes": get_top_rated_dishes(),
            }
        }

    if intent == "feedback_general":
        return {
            "intent": intent,
            "data": {
                "top_rated_dishes": get_top_rated_dishes(),
                "recent_feedbacks": get_recent_feedbacks(),
            }
        }

    # --- General lookup (keyword match → fallback) ---
    matched = get_menu_item_details(message)
    if matched:
        return {
            "intent": "general_lookup",
            "data": {
                "matched_menu_items": matched,
                "similar_items": get_similar_items(message),
            }
        }

    return {
        "intent": "fallback",
        "data": {
            "available_menu_items": get_available_menu_items(limit=15),
            "most_ordered_dishes": get_most_ordered_dishes(limit=3),
            "categories": get_menu_categories(),
        }
    }


# ----------------------------
# System prompt
# ----------------------------

def system_prompt() -> str:
    return """
You are a knowledgeable, friendly, and helpful restaurant assistant.
Your goal is to answer EVERY question a guest could possibly ask about this restaurant.

## Core rules
- Answer ONLY from the structured database facts provided in STRUCTURED DATABASE FACTS.
- NEVER invent dishes, prices, ingredients, ratings, or order details.
- If data is missing or not in the facts, say so clearly and offer an alternative (e.g., suggest calling the restaurant).
- Be concise, warm, and conversational — like a great waiter.

## What you can help with
- Full menu browsing, dish details, ingredients, pricing
- Dietary options: vegetarian, vegan, gluten-free, halal, spicy, non-spicy, seafood, chicken, beef, desserts
- Recommendations: popular dishes, top-rated dishes, chef picks, new items
- Budget-based suggestions ("what can I get for under $15?")
- Category browsing ("show me all starters")
- Combo / pairing suggestions
- Customer's own order history and favorites
- Restaurant feedback and reviews
- Order statistics (for staff/admin queries)
- Greetings, help, and general restaurant questions

## Response style
- When listing multiple dishes, use a clear, scannable format.
- Always mention price when showing dishes unless the user didn't ask.
- If no exact match, offer the closest available option and acknowledge the mismatch.
- If multiple dishes match a query, list all of them.
- For dietary queries, note if nothing matches and suggest alternatives.
- For missing restaurant info (hours, location), politely acknowledge you don't have that data and suggest contacting the restaurant.
- Never say "I don't know" without offering something helpful in its place.
""".strip()


# ----------------------------
# Main entrypoint
# ----------------------------

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
                "content": f"STRUCTURED DATABASE FACTS:\n{context}",
            },
            {
                "role": "user",
                "content": message,
            },
        ],
    )

    return response.choices[0].message.content.strip()