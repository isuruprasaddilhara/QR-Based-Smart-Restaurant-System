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


class DashboardSummarySerializer(serializers.Serializer):
    total_revenue_today = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_orders_today = serializers.IntegerField()
    average_order_value_today = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_orders = serializers.IntegerField()
    preparing_orders = serializers.IntegerField()
    active_tables = serializers.IntegerField()
    total_tables = serializers.IntegerField()
    average_rating = serializers.FloatField(allow_null=True)
    top_item_today = serializers.CharField(allow_null=True)
    revenue_this_week = serializers.DecimalField(max_digits=12, decimal_places=2)
    revenue_this_month = serializers.DecimalField(max_digits=12, decimal_places=2)