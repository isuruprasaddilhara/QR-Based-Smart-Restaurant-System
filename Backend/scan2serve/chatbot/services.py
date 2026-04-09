from decimal import Decimal
from typing import Dict, List

from django.conf import settings
from django.db.models import Avg, Count, Q, Sum
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
    cleaned = (
        normalize(message)
        .replace(",", " ")
        .replace(".", " ")
        .replace("?", " ")
        .replace("!", " ")
        .replace("-", " ")
    )
    words = [w.strip() for w in cleaned.split() if len(w.strip()) >= 3]
    return list(dict.fromkeys(words))


# ----------------------------
# Menu queries
# ----------------------------

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
        MenuItem.objects.select_related("category")
        .filter(query)
        .distinct()
    )


def get_available_menu_items(limit: int = 15) -> List[Dict]:
    items = (
        MenuItem.objects.select_related("category")
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
    return list(MenuCategory.objects.order_by("name").values_list("name", flat=True))


# ----------------------------
# Analytics / calculations
# ----------------------------

def get_most_ordered_dishes(limit: int = 5):
    rows = (
        OrderItem.objects
        .values("menu_item__id", "menu_item__name")
        .annotate(order_count=Count("id"))   # 🔥 changed from Sum → Count
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
                "price": f"{item.price:.2f}",
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
            review_count=Count("orderitem__order__feedback")
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

    avg_feedback = (
        Feedback.objects.aggregate(avg=Avg("rating")).get("avg")
    )

    return {
        "total_orders": total_orders,
        "completed_orders": completed_orders,
        "pending_orders": pending_orders,
        "preparing_orders": preparing_orders,
        "served_orders": served_orders,
        "total_sales": money(total_sales),
        "average_feedback_rating": round(avg_feedback, 2) if avg_feedback is not None else None,
    }


# ----------------------------
# Customer-specific queries
# ----------------------------

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
        items = []
        for item in order.items.all():
            items.append({
                "name": item.menu_item.name,
                "quantity": item.quantity,
                "line_total": money(item.price),
            })

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


# ----------------------------
# Intent routing
# ----------------------------

def detect_intent(message: str) -> str:
    text = normalize(message)

    if contains_any(text, [
        "most ordered", "popular dish", "popular dishes", "best selling",
        "top selling", "most popular", "most ordered dish"
    ]):
        return "popular_dishes"

    if contains_any(text, [
        "top rated", "best rated", "highest rated", "best dish"
    ]):
        return "top_rated_dishes"

    if contains_any(text, [
        "ingredient", "ingredients", "what is in", "contains", "content of"
    ]):
        return "dish_contents"

    if contains_any(text, [
        "price", "cost", "how much"
    ]):
        return "dish_price"

    if contains_any(text, [
        "available", "availability", "do you have", "menu", "show menu"
    ]):
        return "menu_lookup"

    if contains_any(text, [
        "category", "categories"
    ]):
        return "categories"

    if contains_any(text, [
        "my order", "my orders", "order status", "recent orders", "my recent order"
    ]):
        return "user_orders"

    if contains_any(text, [
        "sales", "total orders", "order stats", "statistics", "analytics"
    ]):
        return "order_stats"

    return "general_lookup"


# ----------------------------
# Structured context builder
# ----------------------------

def build_structured_context(user, message: str) -> Dict:
    intent = detect_intent(message)

    if intent == "popular_dishes":
        return {
            "intent": intent,
            "data": {
                "most_ordered_dishes": get_most_ordered_dishes()
            }
        }

    if intent == "top_rated_dishes":
        return {
            "intent": intent,
            "data": {
                "top_rated_dishes": get_top_rated_dishes()
            }
        }

    if intent in {"dish_contents", "dish_price", "menu_lookup", "general_lookup"}:
        matched_items = get_menu_item_details(message)

        if matched_items:
            return {
                "intent": intent,
                "data": {
                    "matched_menu_items": matched_items
                }
            }

        return {
            "intent": intent,
            "data": {
                "available_menu_items": get_available_menu_items()
            }
        }

    if intent == "categories":
        return {
            "intent": intent,
            "data": {
                "categories": get_menu_categories()
            }
        }

    if intent == "user_orders":
        return {
            "intent": intent,
            "data": {
                "user_recent_orders": get_user_recent_orders(user)
            }
        }

    if intent == "order_stats":
        return {
            "intent": intent,
            "data": {
                "order_stats": get_order_stats(),
                "most_ordered_dishes": get_most_ordered_dishes(),
                "top_rated_dishes": get_top_rated_dishes(),
            }
        }

    return {
        "intent": "fallback",
        "data": {
            "available_menu_items": get_available_menu_items(),
            "most_ordered_dishes": get_most_ordered_dishes(3),
        }
    }


# ----------------------------
# OpenAI prompt
# ----------------------------

def system_prompt() -> str:
    return (
        "You are a reliable restaurant assistant for customers. "
        "You must answer only from the structured database facts provided to you. "
        "Never invent dishes, prices, ingredients, popularity, ratings, or order details. "
        "If the data is missing, say that clearly. "
        "Be concise, friendly, and accurate. "
        "If multiple dishes match, mention them clearly."
    )


def ask_chatbot(user, message: str) -> str:
    context = build_structured_context(user, message)

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
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

    return response.output_text.strip()