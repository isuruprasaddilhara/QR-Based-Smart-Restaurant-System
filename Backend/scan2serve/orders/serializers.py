from rest_framework import serializers
from .models import Order, OrderItem, Feedback


class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'menu_item', 'menu_item_name', 'quantity', 'price']


class OrderItemCreateSerializer(serializers.ModelSerializer):
    """Used only during order creation — price is derived from MenuItem, not user input."""
    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity']


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'rating', 'comment']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    feedback = FeedbackSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'table', 'user', 'status', 'total_amount',
            'special_notes', 'created_at', 'items', 'feedback'
        ]
        read_only_fields = ['total_amount', 'created_at']


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True, write_only=True)
    guest_token = serializers.CharField(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'table', 'user', 'special_notes', 'items','guest_token']

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("An order must have at least one item.")
        return items

    def create(self, validated_data):
        items_data = validated_data.pop('items')

        # Derive price from MenuItem and calculate total
        total = 0
        enriched_items = []
        for item in items_data:
            menu_item = item['menu_item']

            if not menu_item.availability:
                raise serializers.ValidationError(
                    f"'{menu_item.name}' is currently unavailable."
                )

            unit_price = menu_item.price
            quantity = item['quantity']
            line_total = unit_price * quantity
            total += line_total
            enriched_items.append({
                'menu_item': menu_item,
                'quantity': quantity,
                'price': line_total,   # price stored as line total (unit * qty)
            })

        order = Order.objects.create(total_amount=total, **validated_data)

        for item_data in enriched_items:
            OrderItem.objects.create(order=order, **item_data)

        return order


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'status']

    def validate_status(self, value):
        valid = [choice[0] for choice in Order.STATUS_CHOICES]
        if value not in valid:
            raise serializers.ValidationError(f"Status must be one of: {valid}")
        return value

class CashierBillRequestSerializer(serializers.ModelSerializer):
    table_id = serializers.IntegerField(source='table.id', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'table_id', 'user_id', 'total_amount', 'status']