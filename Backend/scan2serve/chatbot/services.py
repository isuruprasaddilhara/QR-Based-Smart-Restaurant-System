# services.py

import json
from decimal import Decimal
from typing import Dict, List, Optional, Any

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
from django.utils import timezone

from openai import OpenAI

from menu.models import MenuItem, MenuCategory
from orders.models import Order, OrderItem, Feedback
from favourites.models import FavoriteMenuItem
from tables.models import Table

client = OpenAI(api_key=settings.OPENAI_API_KEY)


# =========================================================
# HELPERS
# =========================================================

def money(value) -> str:
    if value is None:
        return "0.00"

    if isinstance(value, Decimal):
        return f"{value:.2f}"

    return str(value)


def normalize(text: str) -> str:
    return (text or "").strip().lower()


# =========================================================
# MENU ENGINE
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

    queryset = MenuItem.objects.select_related("category")

    if keywords:
        queryset = queryset.filter(query)

    if category:
        queryset = queryset.filter(category__name__icontains=category)

    if min_price is not None:
        queryset = queryset.filter(price__gte=min_price)

    if max_price is not None:
        queryset = queryset.filter(price__lte=max_price)

    if available_only:
        queryset = queryset.filter(availability=True)

    if ingredients:
        ingredient_query = Q()

        for ingredient in ingredients:
            ingredient_query |= Q(ingredients__icontains=ingredient)

        queryset = queryset.filter(ingredient_query)

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


def get_menu_categories():
    return list(
        MenuCategory.objects.order_by("name").values_list("name", flat=True)
    )


# =========================================================
# POPULAR / TOP RATED
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


def get_top_rated_dishes(limit=5):
    rows = (
        MenuItem.objects
        .annotate(
            avg_rating=Avg("orderitem__order__feedback__rating"),
            review_count=Count("orderitem__order__feedback"),
        )
        .filter(review_count__gt=0)
        .order_by("-avg_rating", "-review_count")[:limit]
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
# RECOMMENDATION ENGINE
# =========================================================

def get_personalized_recommendations(user, limit=5):
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
            .filter(availability=True)[:limit]
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
# USER ORDERS
# =========================================================

def get_user_recent_orders(user, limit=5):
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
        items = []

        for item in order.items.all():
            line_total = item.price * item.quantity

            items.append({
                "dish": item.menu_item.name,
                "quantity": item.quantity,
                "unit_price": money(item.price),
                "line_total": money(line_total),
            })

        data.append({
            "order_id": order.id,
            "status": order.status,
            "table": order.table.table_number if order.table else None,
            "total_amount": money(order.total_amount),
            "special_notes": order.special_notes or "",
            "created_at": str(order.created_at),
            "items": items,
        })

    return data


# =========================================================
# TABLES
# =========================================================

def get_available_tables(capacity=None):
    tables = Table.objects.filter(status=False)

    if capacity:
        tables = tables.filter(capacity__gte=capacity)

    return [
        {
            "table_number": table.table_number,
            "section": table.section,
            "capacity": table.capacity,
        }
        for table in tables
    ]


def get_occupied_tables():
    tables = Table.objects.filter(status=True)

    return [
        {
            "table_number": table.table_number,
            "section": table.section,
            "capacity": table.capacity,
        }
        for table in tables
    ]


# =========================================================
# ANALYTICS
# =========================================================

def get_order_statistics():
    total_orders = Order.objects.count()

    total_sales = (
        Order.objects
        .filter(status="completed")
        .aggregate(total=Sum("total_amount"))
        .get("total")
    ) or Decimal("0.00")

    pending = Order.objects.filter(status="pending").count()
    preparing = Order.objects.filter(status="preparing").count()
    served = Order.objects.filter(status="served").count()
    completed = Order.objects.filter(status="completed").count()

    average_rating = (
        Feedback.objects.aggregate(avg=Avg("rating")).get("avg")
    )

    return {
        "total_orders": total_orders,
        "total_sales": money(total_sales),
        "pending_orders": pending,
        "preparing_orders": preparing,
        "served_orders": served,
        "completed_orders": completed,
        "average_rating": round(average_rating, 2)
        if average_rating
        else None,
    }


def get_sales_by_category():
    rows = (
        OrderItem.objects
        .values("menu_item__category__name")
        .annotate(
            revenue=Sum(
                ExpressionWrapper(
                    F("price") * F("quantity"),
                    output_field=DecimalField(),
                )
            )
        )
        .order_by("-revenue")
    )

    return [
        {
            "category": row["menu_item__category__name"],
            "revenue": money(row["revenue"]),
        }
        for row in rows
    ]


# =========================================================
# FEEDBACK ANALYSIS
# =========================================================

def get_feedback_summary(limit=10):
    feedbacks = (
        Feedback.objects
        .select_related("order")
        .exclude(comment="")
        .order_by("-id")[:limit]
    )

    return [
        {
            "rating": feedback.rating,
            "comment": feedback.comment,
            "order_id": feedback.order.id,
        }
        for feedback in feedbacks
    ]


# =========================================================
# TOOL FUNCTIONS
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
                        "items": {"type": "string"},
                    },
                    "category": {"type": "string"},
                    "min_price": {"type": "number"},
                    "max_price": {"type": "number"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_popular_dishes",
            "description": "Get most ordered dishes",
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
            "name": "get_user_orders",
            "description": "Get recent orders of authenticated user",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_tables",
            "description": "Get available tables",
            "parameters": {
                "type": "object",
                "properties": {
                    "capacity": {"type": "integer"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_analytics",
            "description": "Get restaurant analytics",
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

def execute_tool(tool_name, arguments, user):
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

    if tool_name == "get_user_orders":
        return get_user_recent_orders(user)

    if tool_name == "get_tables":
        return get_available_tables(
            capacity=arguments.get("capacity")
        )

    if tool_name == "get_analytics":
        return {
            "stats": get_order_statistics(),
            "sales_by_category": get_sales_by_category(),
            "popular_dishes": get_most_ordered_dishes(),
        }

    return {"error": "Unknown tool"}


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
- NEVER hallucinate dishes, prices, or analytics
- If information is unavailable, say clearly
- Be conversational and concise
- Recommend dishes intelligently
- Personalize responses when possible

Capabilities:
- Menu search
- Dish recommendations
- Order tracking
- Analytics
- Table availability
- Ratings and popularity
- Customer history

Current user role: {role}
"""


# =========================================================
# MAIN CHATBOT
# =========================================================

def ask_chatbot(user, message: str) -> str:
    messages = [
        {
            "role": "system",
            "content": build_system_prompt(user),
        },
        {
            "role": "user",
            "content": message,
        },
    ]

    first_response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    response_message = first_response.choices[0].message

    tool_calls = response_message.tool_calls

    if tool_calls:
        messages.append(response_message)

        for tool_call in tool_calls:
            tool_name = tool_call.function.name

            arguments = json.loads(tool_call.function.arguments)

            result = execute_tool(
                tool_name,
                arguments,
                user,
            )

            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": tool_name,
                "content": json.dumps(result),
            })

        final_response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
        )

        return final_response.choices[0].message.content

    return response_message.content