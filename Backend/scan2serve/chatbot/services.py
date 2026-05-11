from decimal import Decimal
from typing import Dict, List, Optional

from django.conf import settings
from django.db.models import Avg, Count, Q, Sum, F, Min, Max
from django.utils import timezone
from openai import OpenAI

from menu.models import MenuItem, MenuCategory
from orders.models import Order, OrderItem, Feedback
from tables.models import Table
from users.models import User
from favourites.models import FavoriteMenuItem

client = OpenAI(api_key=settings.OPENAI_API_KEY)


# ─────────────────────────────────────────────
# Small helpers
# ─────────────────────────────────────────────

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
    stop_words = {"the", "and", "for", "are", "you", "what", "how", "can", "have", "has", "was", "this", "that"}
    words = [w.strip() for w in cleaned.split() if len(w.strip()) >= 3 and w.strip() not in stop_words]
    return list(dict.fromkeys(words))


# ─────────────────────────────────────────────
# Menu queries
# ─────────────────────────────────────────────

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


def get_available_menu_items(limit: int = 20) -> List[Dict]:
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
            "image_url": item.image_url or None,
        }
        for item in items
    ]


def get_unavailable_menu_items() -> List[Dict]:
    items = (
        MenuItem.objects.select_related("category")
        .filter(availability=False)
        .order_by("category__name", "name")
    )
    return [
        {"name": item.name, "category": item.category.name, "price": money(item.price)}
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
            "image_url": item.image_url or None,
        }
        for item in items
    ]


def get_menu_categories() -> List[Dict]:
    categories = MenuCategory.objects.annotate(
        item_count=Count("menuitem"),
        available_count=Count("menuitem", filter=Q(menuitem__availability=True)),
    ).order_by("name")
    return [
        {
            "name": c.name,
            "total_items": c.item_count,
            "available_items": c.available_count,
        }
        for c in categories
    ]


def get_items_by_category(message: str) -> List[Dict]:
    keywords = extract_keywords(message)
    category_query = Q()
    for kw in keywords:
        category_query |= Q(name__icontains=kw)

    categories = MenuCategory.objects.filter(category_query)
    items = (
        MenuItem.objects.select_related("category")
        .filter(category__in=categories)
        .order_by("name")
    )
    return [
        {
            "name": item.name,
            "category": item.category.name,
            "price": money(item.price),
            "available": item.availability,
            "description": item.description or "N/A",
        }
        for item in items
    ]


def get_price_range_items(min_price: Optional[float] = None, max_price: Optional[float] = None) -> List[Dict]:
    qs = MenuItem.objects.select_related("category").filter(availability=True)
    if min_price is not None:
        qs = qs.filter(price__gte=min_price)
    if max_price is not None:
        qs = qs.filter(price__lte=max_price)
    qs = qs.order_by("price")
    return [
        {"name": item.name, "category": item.category.name, "price": money(item.price)}
        for item in qs
    ]


def get_cheapest_items(limit: int = 5) -> List[Dict]:
    items = (
        MenuItem.objects.select_related("category")
        .filter(availability=True)
        .order_by("price")[:limit]
    )
    return [
        {"name": item.name, "category": item.category.name, "price": money(item.price)}
        for item in items
    ]


def get_most_expensive_items(limit: int = 5) -> List[Dict]:
    items = (
        MenuItem.objects.select_related("category")
        .filter(availability=True)
        .order_by("-price")[:limit]
    )
    return [
        {"name": item.name, "category": item.category.name, "price": money(item.price)}
        for item in items
    ]


# ─────────────────────────────────────────────
# Analytics / popularity
# ─────────────────────────────────────────────

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


def get_least_ordered_dishes(limit: int = 5) -> List[Dict]:
    rows = (
        OrderItem.objects
        .values("menu_item__id", "menu_item__name")
        .annotate(order_count=Count("id"))
        .order_by("order_count")[:limit]
    )
    return [{"name": r["menu_item__name"], "times_ordered": r["order_count"]} for r in rows]


def get_revenue_by_category() -> List[Dict]:
    rows = (
        OrderItem.objects
        .select_related("menu_item__category")
        .filter(order__status="completed")
        .values("menu_item__category__name")
        .annotate(total_revenue=Sum(F("price") * F("quantity")))
        .order_by("-total_revenue")
    )
    return [
        {"category": r["menu_item__category__name"], "total_revenue": money(r["total_revenue"])}
        for r in rows
    ]


# ─────────────────────────────────────────────
# Order stats
# ─────────────────────────────────────────────

def get_order_stats() -> Dict:
    total_orders = Order.objects.count()
    completed = Order.objects.filter(status="completed").count()
    pending = Order.objects.filter(status="pending").count()
    preparing = Order.objects.filter(status="preparing").count()
    served = Order.objects.filter(status="served").count()
    requested = Order.objects.filter(status="requested").count()

    total_sales = (
        Order.objects.filter(status="completed")
        .aggregate(total=Sum("total_amount"))
        .get("total") or Decimal("0.00")
    )
    avg_order_value = (
        Order.objects.filter(status="completed")
        .aggregate(avg=Avg("total_amount"))
        .get("avg")
    )
    avg_feedback = Feedback.objects.aggregate(avg=Avg("rating")).get("avg")

    return {
        "total_orders": total_orders,
        "completed_orders": completed,
        "pending_orders": pending,
        "preparing_orders": preparing,
        "served_orders": served,
        "requested_orders": requested,
        "total_sales": money(total_sales),
        "average_order_value": money(avg_order_value) if avg_order_value else "N/A",
        "average_feedback_rating": round(avg_feedback, 2) if avg_feedback is not None else None,
    }


def get_recent_feedback(limit: int = 5) -> List[Dict]:
    feedbacks = (
        Feedback.objects.select_related("order__user")
        .order_by("-order__created_at")[:limit]
    )
    return [
        {
            "order_id": f.order.id,
            "rating": f.rating,
            "comment": f.comment or "No comment",
            "customer": f.order.user.name if f.order.user else "Guest",
        }
        for f in feedbacks
    ]


def get_low_rated_feedback(threshold: int = 3, limit: int = 5) -> List[Dict]:
    feedbacks = (
        Feedback.objects.select_related("order")
        .filter(rating__lt=threshold)
        .order_by("rating")[:limit]
    )
    return [
        {"order_id": f.order.id, "rating": f.rating, "comment": f.comment or "No comment"}
        for f in feedbacks
    ]


# ─────────────────────────────────────────────
# Table queries
# ─────────────────────────────────────────────

def get_table_status() -> Dict:
    total = Table.objects.count()
    occupied = Table.objects.filter(status=True).count()
    available = Table.objects.filter(status=False).count()
    return {
        "total_tables": total,
        "occupied_tables": occupied,
        "available_tables": available,
    }


def get_available_tables() -> List[Dict]:
    tables = Table.objects.filter(status=False).order_by("table_number")
    return [
        {
            "table_number": t.table_number,
            "section": t.section or "N/A",
            "capacity": t.capacity,
        }
        for t in tables
    ]


def get_table_details(message: str) -> List[Dict]:
    keywords = extract_keywords(message)
    query = Q()
    for kw in keywords:
        query |= Q(section__icontains=kw)
        if kw.isdigit():
            query |= Q(table_number=int(kw))

    tables = Table.objects.filter(query)
    return [
        {
            "table_number": t.table_number,
            "section": t.section or "N/A",
            "capacity": t.capacity,
            "status": "Occupied" if t.status else "Available",
        }
        for t in tables
    ]


# ─────────────────────────────────────────────
# Customer-specific queries
# ─────────────────────────────────────────────

def get_user_recent_orders(user, limit: int = 5) -> List[Dict]:
    if not user or not user.is_authenticated:
        return []

    orders = (
        Order.objects.select_related("table")
        .prefetch_related("items__menu_item", "feedback")
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
        feedback = None
        if hasattr(order, "feedback"):
            feedback = {"rating": order.feedback.rating, "comment": order.feedback.comment}

        data.append({
            "order_id": order.id,
            "status": order.status,
            "total_amount": money(order.total_amount),
            "table_number": order.table.table_number if order.table else None,
            "special_notes": order.special_notes or "",
            "created_at": str(order.created_at),
            "items": items,
            "feedback": feedback,
        })

    return data


def get_user_order_by_id(user, order_id: int) -> Optional[Dict]:
    try:
        order = (
            Order.objects.select_related("table")
            .prefetch_related("items__menu_item", "feedback")
            .get(id=order_id, user=user)
        )
    except Order.DoesNotExist:
        return None

    items = [
        {"name": i.menu_item.name, "quantity": i.quantity, "line_total": money(i.price)}
        for i in order.items.all()
    ]
    feedback = None
    if hasattr(order, "feedback"):
        feedback = {"rating": order.feedback.rating, "comment": order.feedback.comment}

    return {
        "order_id": order.id,
        "status": order.status,
        "total_amount": money(order.total_amount),
        "table_number": order.table.table_number if order.table else None,
        "special_notes": order.special_notes or "",
        "created_at": str(order.created_at),
        "preparing_at": str(order.preparing_at) if order.preparing_at else None,
        "served_at": str(order.served_at) if order.served_at else None,
        "completed_at": str(order.completed_at) if order.completed_at else None,
        "items": items,
        "feedback": feedback,
    }


def get_user_spending_summary(user) -> Dict:
    if not user or not user.is_authenticated:
        return {}

    agg = (
        Order.objects.filter(user=user, status="completed")
        .aggregate(
            total_spent=Sum("total_amount"),
            order_count=Count("id"),
            avg_order=Avg("total_amount"),
        )
    )
    return {
        "total_spent": money(agg["total_spent"]),
        "total_orders": agg["order_count"] or 0,
        "average_order_value": money(agg["avg_order"]),
    }


def get_user_favorites(user) -> List[Dict]:
    if not user or not user.is_authenticated:
        return []

    favs = (
        FavoriteMenuItem.objects.select_related("menu_item__category")
        .filter(user=user)
        .order_by("-created_at")
    )
    return [
        {
            "name": f.menu_item.name,
            "category": f.menu_item.category.name,
            "price": money(f.menu_item.price),
            "available": f.menu_item.availability,
            "saved_at": str(f.created_at),
        }
        for f in favs
    ]


def get_user_profile(user) -> Dict:
    if not user or not user.is_authenticated:
        return {}
    return {
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "phone": user.phone_no or "N/A",
        "member_since": str(user.created_at),
    }


# ─────────────────────────────────────────────
# Staff / admin queries
# ─────────────────────────────────────────────

def get_active_orders() -> List[Dict]:
    orders = (
        Order.objects.select_related("table", "user")
        .prefetch_related("items__menu_item")
        .filter(status__in=["pending", "preparing", "served", "requested"])
        .order_by("created_at")
    )
    result = []
    for order in orders:
        items = [
            {"name": i.menu_item.name, "quantity": i.quantity}
            for i in order.items.all()
        ]
        result.append({
            "order_id": order.id,
            "status": order.status,
            "table_number": order.table.table_number if order.table else None,
            "customer": order.user.name if order.user else "Guest",
            "created_at": str(order.created_at),
            "special_notes": order.special_notes or "",
            "items": items,
        })
    return result


def get_staff_list() -> List[Dict]:
    staff = User.objects.filter(role__in=["cashier", "kitchen", "admin"]).order_by("role", "name")
    return [
        {"name": u.name, "role": u.role, "email": u.email}
        for u in staff
    ]


def get_customer_count() -> Dict:
    return {
        "total_customers": User.objects.filter(role="customer").count(),
        "total_staff": User.objects.filter(role__in=["cashier", "kitchen", "admin"]).count(),
    }


# ─────────────────────────────────────────────
# Intent detection
# ─────────────────────────────────────────────

def detect_intent(user, message: str) -> str:
    text = normalize(message)

    if contains_any(text, ["most ordered", "popular dish", "popular dishes", "best selling",
                            "top selling", "most popular", "trending"]):
        return "popular_dishes"

    if contains_any(text, ["top rated", "best rated", "highest rated", "best dish", "most reviewed"]):
        return "top_rated_dishes"

    if contains_any(text, ["least ordered", "slow moving", "unpopular"]):
        return "least_ordered_dishes"

    if contains_any(text, ["cheapest", "cheap", "budget", "lowest price", "affordable"]):
        return "cheapest_items"

    if contains_any(text, ["expensive", "priciest", "most expensive", "premium"]):
        return "expensive_items"

    if contains_any(text, ["ingredient", "ingredients", "what is in", "contains", "content of", "made of", "allergen"]):
        return "dish_contents"

    if contains_any(text, ["price", "cost", "how much"]):
        return "dish_price"

    if contains_any(text, ["not available", "unavailable", "out of stock", "sold out"]):
        return "unavailable_items"

    if contains_any(text, ["available", "availability", "do you have", "menu", "show menu", "what's on"]):
        return "menu_lookup"

    if contains_any(text, ["category", "categories", "type of food", "food type"]):
        return "categories"

    if contains_any(text, ["items in", "dishes in", "food in", "what is in the", "show me"]) and \
            contains_any(text, [c.lower() for c in MenuCategory.objects.values_list("name", flat=True)]):
        return "category_items"

    if contains_any(text, ["my order", "my orders", "order status", "recent order", "my recent"]):
        return "user_orders"

    if contains_any(text, ["order", "status"]) and any(c.isdigit() for c in text):
        return "order_by_id"

    if contains_any(text, ["my spending", "how much have i spent", "total spent", "my total", "my bill"]):
        return "user_spending"

    if contains_any(text, ["my favourite", "my favorite", "saved items", "my saved", "wishlist"]):
        return "user_favorites"

    if contains_any(text, ["my profile", "my account", "my details", "who am i"]):
        return "user_profile"

    if contains_any(text, ["table", "tables", "seating", "seat", "section"]):
        return "table_status"

    if contains_any(text, ["feedback", "reviews", "complaints", "ratings", "bad review"]):
        return "feedback_summary"

    if contains_any(text, ["revenue", "earnings", "income", "sales by category"]):
        return "revenue_by_category"

    if contains_any(text, ["sales", "total orders", "order stats", "statistics", "analytics", "overview"]):
        return "order_stats"

    if contains_any(text, ["active order", "current order", "kitchen", "pending order"]) and \
            user and user.role in ["admin", "cashier", "kitchen"]:
        return "active_orders"

    if contains_any(text, ["staff", "employee", "team", "workers"]) and \
            user and user.role == "admin":
        return "staff_list"

    if contains_any(text, ["customer count", "how many customers", "user count"]) and \
            user and user.role == "admin":
        return "customer_count"

    return "general_lookup"


# ─────────────────────────────────────────────
# Context builder
# ─────────────────────────────────────────────

def extract_order_id(message: str) -> Optional[int]:
    import re
    match = re.search(r'\b(\d+)\b', message)
    return int(match.group(1)) if match else None


def build_structured_context(user, message: str) -> Dict:
    intent = detect_intent(user, message)

    if intent == "popular_dishes":
        return {"intent": intent, "data": {"most_ordered_dishes": get_most_ordered_dishes()}}

    if intent == "top_rated_dishes":
        return {"intent": intent, "data": {"top_rated_dishes": get_top_rated_dishes()}}

    if intent == "least_ordered_dishes":
        return {"intent": intent, "data": {"least_ordered_dishes": get_least_ordered_dishes()}}

    if intent == "cheapest_items":
        return {"intent": intent, "data": {"cheapest_items": get_cheapest_items()}}

    if intent == "expensive_items":
        return {"intent": intent, "data": {"most_expensive_items": get_most_expensive_items()}}

    if intent == "unavailable_items":
        return {"intent": intent, "data": {"unavailable_items": get_unavailable_menu_items()}}

    if intent in {"dish_contents", "dish_price", "menu_lookup", "general_lookup"}:
        matched = get_menu_item_details(message)
        if matched:
            return {"intent": intent, "data": {"matched_menu_items": matched}}
        return {"intent": intent, "data": {"available_menu_items": get_available_menu_items()}}

    if intent == "categories":
        return {"intent": intent, "data": {"categories": get_menu_categories()}}

    if intent == "category_items":
        return {"intent": intent, "data": {"category_items": get_items_by_category(message)}}

    if intent == "user_orders":
        return {"intent": intent, "data": {"user_recent_orders": get_user_recent_orders(user)}}

    if intent == "order_by_id":
        order_id = extract_order_id(message)
        if order_id:
            order = get_user_order_by_id(user, order_id)
            return {"intent": intent, "data": {"order": order or "Order not found."}}
        return {"intent": intent, "data": {"error": "Could not determine which order you meant."}}

    if intent == "user_spending":
        return {"intent": intent, "data": {"spending_summary": get_user_spending_summary(user)}}

    if intent == "user_favorites":
        return {"intent": intent, "data": {"favorites": get_user_favorites(user)}}

    if intent == "user_profile":
        return {"intent": intent, "data": {"profile": get_user_profile(user)}}

    if intent == "table_status":
        return {
            "intent": intent,
            "data": {
                "table_overview": get_table_status(),
                "available_tables": get_available_tables(),
                "table_details": get_table_details(message),
            }
        }

    if intent == "feedback_summary":
        return {
            "intent": intent,
            "data": {
                "recent_feedback": get_recent_feedback(),
                "low_rated_feedback": get_low_rated_feedback(),
            }
        }

    if intent == "revenue_by_category":
        return {"intent": intent, "data": {"revenue_by_category": get_revenue_by_category()}}

    if intent == "order_stats":
        return {
            "intent": intent,
            "data": {
                "order_stats": get_order_stats(),
                "most_ordered_dishes": get_most_ordered_dishes(3),
                "top_rated_dishes": get_top_rated_dishes(3),
                "revenue_by_category": get_revenue_by_category(),
            }
        }

    if intent == "active_orders":
        return {"intent": intent, "data": {"active_orders": get_active_orders()}}

    if intent == "staff_list":
        return {"intent": intent, "data": {"staff": get_staff_list()}}

    if intent == "customer_count":
        return {"intent": intent, "data": {"user_counts": get_customer_count()}}

    # Fallback: provide broad context
    return {
        "intent": "fallback",
        "data": {
            "available_menu_items": get_available_menu_items(10),
            "most_ordered_dishes": get_most_ordered_dishes(3),
            "categories": get_menu_categories(),
        }
    }


# ─────────────────────────────────────────────
# System prompt
# ─────────────────────────────────────────────

def system_prompt(user) -> str:
    role = getattr(user, "role", "guest") if user and getattr(user, "is_authenticated", False) else "guest"

    base = (
        "You are a helpful and friendly restaurant assistant. "
        "Answer only using the structured database facts provided — never invent dishes, prices, ingredients, ratings, or order details. "
        "If the data is missing or empty, say so clearly. "
        "Be concise and accurate. If multiple dishes match a question, list them clearly.\n\n"
    )

    role_instructions = {
        "admin": (
            "You are speaking with an admin. You may share full analytics, staff lists, order statistics, "
            "revenue data, active orders, customer counts, and feedback summaries."
        ),
        "cashier": (
            "You are speaking with a cashier. You may share active orders, table status, order stats, "
            "and menu details, but not detailed staff management data."
        ),
        "kitchen": (
            "You are speaking with kitchen staff. Focus on active orders, item details, and ingredients. "
            "Do not share sales or customer account details."
        ),
        "customer": (
            "You are speaking with a customer. Help them explore the menu, find dishes, check their own "
            "orders, view their favourites, and understand pricing. Do not share other customers' data or internal analytics."
        ),
        "guest": (
            "You are speaking with a guest (not logged in). You can answer questions about the menu, "
            "categories, pricing, and popular dishes. You cannot show order history or favourites."
        ),
    }

    return base + role_instructions.get(role, role_instructions["guest"])


# ─────────────────────────────────────────────
# Main entrypoint
# ─────────────────────────────────────────────

def ask_chatbot(user, message: str) -> str:
    context = build_structured_context(user, message)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": system_prompt(user),
            },
            {
                "role": "system",
                "content": f"STRUCTURED DATABASE FACTS (use only these):\n{context}",
            },
            {
                "role": "user",
                "content": message,
            },
        ],
    )

    return response.choices[0].message.content.strip()