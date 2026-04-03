from decimal import Decimal
from django.conf import settings
from django.db.models import Q
from openai import OpenAI

from menu.models import MenuItem, MenuCategory
from orders.models import Order

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def _format_money(value):
    if value is None:
        return "0.00"
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    return str(value)


def build_system_prompt():
    return (
        "You are a helpful chatbot for a restaurant management application. "
        "Answer only from the provided database context. "
        "Do not invent menu items, prices, order statuses, tables, or any other facts. "
        "If the answer is not available in the context, say clearly that the information is not available. "
        "Keep answers short, clear, and helpful."
    )


def extract_keywords(message: str):
    words = []
    for word in message.lower().replace(",", " ").replace(".", " ").split():
        word = word.strip()
        if len(word) >= 3:
            words.append(word)
    return list(set(words))


def get_menu_context(message: str) -> str:
    """
    Return menu-related context based on the user's message.
    """
    message_lower = message.lower()
    keywords = extract_keywords(message)

    menu_query_words = {
        "menu", "food", "drink", "price", "available", "availability",
        "item", "items", "dish", "dishes", "burger", "pizza", "rice",
        "coffee", "tea", "juice", "category", "categories", "ingredient",
        "ingredients"
    }

    should_search_menu = any(word in message_lower for word in menu_query_words)

    query = Q()
    for word in keywords:
        query |= Q(name__icontains=word)
        query |= Q(description__icontains=word)
        query |= Q(ingredients__icontains=word)
        query |= Q(category__name__icontains=word)

    matched_items = MenuItem.objects.select_related("category").filter(query).distinct()[:10] if query else MenuItem.objects.none()

    if matched_items.exists():
        lines = []
        for item in matched_items:
            lines.append(
                f"- {item.name} | Category: {item.category.name} | "
                f"Price: {_format_money(item.price)} | Available: {item.availability} | "
                f"Ingredients: {item.ingredients or 'N/A'}"
            )
        return "MATCHED MENU ITEMS:\n" + "\n".join(lines)

    if should_search_menu:
        available_items = (
            MenuItem.objects.select_related("category")
            .filter(availability=True)
            .order_by("category__name", "name")[:15]
        )

        if available_items.exists():
            lines = []
            for item in available_items:
                lines.append(
                    f"- {item.name} | Category: {item.category.name} | Price: {_format_money(item.price)}"
                )
            return "AVAILABLE MENU ITEMS:\n" + "\n".join(lines)

    return ""


def get_category_context(message: str) -> str:
    message_lower = message.lower()
    if "category" not in message_lower and "categories" not in message_lower:
        return ""

    categories = MenuCategory.objects.order_by("name")
    if not categories.exists():
        return "MENU CATEGORIES:\n- No categories found."

    lines = [f"- {category.name}" for category in categories]
    return "MENU CATEGORIES:\n" + "\n".join(lines)


def get_order_context(user, message: str) -> str:
    """
    Return user-specific order context.
    Only authenticated users can see their own orders here.
    """
    message_lower = message.lower()

    order_words = {"order", "orders", "status", "bill", "total", "my order", "recent order"}
    if not any(word in message_lower for word in order_words):
        return ""

    if not user or not user.is_authenticated:
        return (
            "ORDER INFO:\n"
            "- User is not authenticated, so personal order data is not available."
        )

    orders = (
        Order.objects.select_related("table", "user")
        .prefetch_related("items__menu_item")
        .filter(user=user)
        .order_by("-created_at")[:5]
    )

    if not orders.exists():
        return "USER RECENT ORDERS:\n- No orders found for this user."

    order_blocks = []
    for order in orders:
        item_lines = []
        for item in order.items.all():
            item_lines.append(
                f"  * {item.menu_item.name} x {item.quantity} | Line Total: {_format_money(item.price)}"
            )

        items_text = "\n".join(item_lines) if item_lines else "  * No items"
        table_id = order.table.id if order.table else "N/A"

        order_blocks.append(
            f"Order #{order.id}\n"
            f"- Status: {order.status}\n"
            f"- Total Amount: {_format_money(order.total_amount)}\n"
            f"- Table: {table_id}\n"
            f"- Special Notes: {order.special_notes or 'N/A'}\n"
            f"- Created At: {order.created_at}\n"
            f"- Items:\n{items_text}"
        )

    return "USER RECENT ORDERS:\n" + "\n\n".join(order_blocks)


def get_table_context(message: str) -> str:
    """
    Optional simple table info based on menu/order/table questions.
    Since your Table model has status, section, capacity.
    """
    from tables.models import Table

    message_lower = message.lower()
    if "table" not in message_lower and "tables" not in message_lower:
        return ""

    tables = Table.objects.order_by("id")[:10]
    if not tables.exists():
        return "TABLE INFO:\n- No tables found."

    lines = []
    for table in tables:
        lines.append(
            f"- Table {table.id} | Occupied: {table.status} | "
            f"Section: {table.section or 'N/A'} | Capacity: {table.capacity}"
        )
    return "TABLE INFO:\n" + "\n".join(lines)


def get_fallback_context() -> str:
    total_categories = MenuCategory.objects.count()
    total_menu_items = MenuItem.objects.count()
    total_available_items = MenuItem.objects.filter(availability=True).count()
    total_orders = Order.objects.count()

    return (
        "APP SUMMARY:\n"
        f"- Total Categories: {total_categories}\n"
        f"- Total Menu Items: {total_menu_items}\n"
        f"- Available Menu Items: {total_available_items}\n"
        f"- Total Orders: {total_orders}"
    )


def build_app_context(user, message: str) -> str:
    parts = []

    menu_context = get_menu_context(message)
    if menu_context:
        parts.append(menu_context)

    category_context = get_category_context(message)
    if category_context:
        parts.append(category_context)

    order_context = get_order_context(user, message)
    if order_context:
        parts.append(order_context)

    table_context = get_table_context(message)
    if table_context:
        parts.append(table_context)

    if not parts:
        parts.append(get_fallback_context())

    return "\n\n".join(parts)


def ask_chatbot(user, message: str) -> str:
    app_context = build_app_context(user, message)

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": build_system_prompt(),
            },
            {
                "role": "system",
                "content": f"APP DATABASE CONTEXT:\n{app_context}",
            },
            {
                "role": "user",
                "content": message,
            },
        ],
    )

    return response.output_text.strip()