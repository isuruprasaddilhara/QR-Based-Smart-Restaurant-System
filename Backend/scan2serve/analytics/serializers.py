from rest_framework import serializers


class RevenueSerializer(serializers.Serializer):
    period = serializers.CharField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    order_count = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)


class TopMenuItemSerializer(serializers.Serializer):
    menu_item__id = serializers.IntegerField()
    menu_item__name = serializers.CharField()
    menu_item__category__name = serializers.CharField()
    total_quantity = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


class CategoryRevenueSerializer(serializers.Serializer):
    menu_item__category__name = serializers.CharField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_quantity = serializers.IntegerField()
    order_count = serializers.IntegerField()


class OrderStatusSummarySerializer(serializers.Serializer):
    status = serializers.CharField()
    count = serializers.IntegerField()


class TablePerformanceSerializer(serializers.Serializer):
    table__id = serializers.IntegerField()
    table__section = serializers.CharField(allow_null=True)
    table__capacity = serializers.IntegerField()
    order_count = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


class FeedbackSummarySerializer(serializers.Serializer):
    average_rating = serializers.FloatField()
    total_feedback_count = serializers.IntegerField()
    rating_1 = serializers.IntegerField()
    rating_2 = serializers.IntegerField()
    rating_3 = serializers.IntegerField()
    rating_4 = serializers.IntegerField()
    rating_5 = serializers.IntegerField()


class HourlyOrderSerializer(serializers.Serializer):
    hour = serializers.IntegerField()
    order_count = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


class PopularItemSerializer(serializers.Serializer):
    menu_item__id = serializers.IntegerField()
    menu_item__name = serializers.CharField()
    total_quantity = serializers.IntegerField()
    total_orders = serializers.IntegerField()


class DailyRevenueSerializer(serializers.Serializer):
    day = serializers.CharField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    order_count = serializers.IntegerField()

class MostOrderedCustomerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()
    phone_no = serializers.CharField(allow_null=True, allow_blank=True)
    total_orders = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)


class DashboardSummarySerializer(serializers.Serializer):
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_orders = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=12, decimal_places=2)

    pending_orders = serializers.IntegerField()
    preparing_orders = serializers.IntegerField()

    peak_time = serializers.CharField(allow_null=True)
    peak_time_order_count = serializers.IntegerField()

    popular_items = PopularItemSerializer(many=True)
    daily_revenue = DailyRevenueSerializer(many=True)

    average_order_processing_time_minutes = serializers.FloatField(allow_null=True)
    most_ordered_customers = MostOrderedCustomerSerializer(many=True)