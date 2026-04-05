from django.shortcuts import render

# Create your views here.
from django.db.models import (
    Sum, Count, Avg, F, ExpressionWrapper, DecimalField, IntegerField
)
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, ExtractHour
from django.utils import timezone
from django.utils.dateparse import parse_date

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from datetime import timedelta, date

from orders.models import Order, OrderItem, Feedback
from tables.models import Table
from menu.models import MenuItem, MenuCategory

from .serializers import (
    RevenueSerializer,
    TopMenuItemSerializer,
    CategoryRevenueSerializer,
    OrderStatusSummarySerializer,
    TablePerformanceSerializer,
    FeedbackSummarySerializer,
    HourlyOrderSerializer,
    DashboardSummarySerializer,
)
from .permissions import IsAdminOrCashier
from .utils import get_date_range


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrCashier]

    def get(self, request):
        start_date, end_date = get_date_range(request)  # ← use shared util

        completed_orders = Order.objects.filter(
            status='completed',
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        )
        agg = completed_orders.aggregate(
            total_revenue=Sum('total_amount'),
            order_count=Count('id'),
        )
        total_revenue = agg['total_revenue'] or 0
        order_count = agg['order_count'] or 0
        avg_order = round(total_revenue / order_count, 2) if order_count else 0

        pending_orders = Order.objects.filter(
            status='pending',
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        ).count()

        preparing_orders = Order.objects.filter(
            status='preparing',
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        ).count()

        active_tables = Table.objects.filter(status=True).count()
        total_tables = Table.objects.count()

        avg_rating = Feedback.objects.filter(
            order__created_at__date__gte=start_date,
            order__created_at__date__lte=end_date,
        ).aggregate(avg=Avg('rating'))['avg']

        top_item = (
            OrderItem.objects.filter(
                order__created_at__date__gte=start_date,
                order__created_at__date__lte=end_date,
            )
            .values('menu_item__name')
            .annotate(total_qty=Sum('quantity'))
            .order_by('-total_qty')
            .first()
        )

        data = {
            'total_revenue_today': total_revenue,
            'total_orders_today': order_count,
            'average_order_value_today': avg_order,
            'pending_orders': pending_orders,
            'preparing_orders': preparing_orders,
            'active_tables': active_tables,
            'total_tables': total_tables,
            'average_rating': round(avg_rating, 2) if avg_rating else None,
            'top_item_today': top_item['menu_item__name'] if top_item else None,
            'revenue_this_week': total_revenue,   # same range now
            'revenue_this_month': total_revenue,  # same range now
        }

        serializer = DashboardSummarySerializer(data)
        return Response(serializer.data)


class RevenueAnalyticsView(APIView):
    """
    Revenue grouped by day / week / month.
    GET /analytics/revenue/?group_by=day&start=YYYY-MM-DD&end=YYYY-MM-DD
    group_by options: day (default), week, month
    """
    permission_classes = [IsAuthenticated, IsAdminOrCashier]

    def get(self, request):
        group_by = request.query_params.get('group_by', 'day')
        start_date, end_date = get_date_range(request)

        qs = Order.objects.filter(
            status='completed',
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        )

        trunc_map = {
            'day': TruncDate,
            'week': TruncWeek,
            'month': TruncMonth,
        }
        trunc_fn = trunc_map.get(group_by, TruncDate)

        results = (
            qs.annotate(period=trunc_fn('created_at'))
            .values('period')
            .annotate(
                total_revenue=Sum('total_amount'),
                order_count=Count('id'),
            )
            .order_by('period')
        )

        data = []
        for row in results:
            order_count = row['order_count']
            total_revenue = row['total_revenue'] or 0
            data.append({
                'period': str(row['period']),
                'total_revenue': total_revenue,
                'order_count': order_count,
                'average_order_value': round(total_revenue / order_count, 2) if order_count else 0,
            })

        serializer = RevenueSerializer(data, many=True)
        return Response(serializer.data)


class TopMenuItemsView(APIView):
    """
    Best-selling menu items by quantity and revenue.
    GET /analytics/menu/top-items/?start=YYYY-MM-DD&end=YYYY-MM-DD&limit=10
    """
    permission_classes = [IsAuthenticated, IsAdminOrCashier]

    def get(self, request):
        start_date, end_date = get_date_range(request)
        limit = int(request.query_params.get('limit', 10))

        results = (
            OrderItem.objects.filter(
                order__status='completed',
                order__created_at__date__gte=start_date,
                order__created_at__date__lte=end_date,
            )
            .values('menu_item__id', 'menu_item__name', 'menu_item__category__name')
            .annotate(
                total_quantity=Sum('quantity'),
                total_revenue=Sum(
                    ExpressionWrapper(
                        F('price') * F('quantity'),
                        output_field=DecimalField(max_digits=12, decimal_places=2)
                    )
                ),
            )
            .order_by('-total_quantity')[:limit]
        )

        serializer = TopMenuItemSerializer(list(results), many=True)
        return Response(serializer.data)


class CategoryRevenueView(APIView):
    """
    Revenue and sales volume broken down by menu category.
    GET /analytics/menu/categories/?start=YYYY-MM-DD&end=YYYY-MM-DD
    """
    permission_classes = [IsAuthenticated, IsAdminOrCashier]

    def get(self, request):
        start_date, end_date = get_date_range(request)

        results = (
            OrderItem.objects.filter(
                order__status='completed',
                order__created_at__date__gte=start_date,
                order__created_at__date__lte=end_date,
            )
            .values('menu_item__category__name')
            .annotate(
                total_revenue=Sum(
                    ExpressionWrapper(
                        F('price') * F('quantity'),
                        output_field=DecimalField(max_digits=12, decimal_places=2)
                    )
                ),
                total_quantity=Sum('quantity'),
                order_count=Count('order', distinct=True),
            )
            .order_by('-total_revenue')
        )

        serializer = CategoryRevenueSerializer(list(results), many=True)
        return Response(serializer.data)


class OrderStatusSummaryView(APIView):
    """
    Count of orders grouped by status.
    GET /analytics/orders/status/?start=YYYY-MM-DD&end=YYYY-MM-DD
    """
    permission_classes = [IsAuthenticated, IsAdminOrCashier]

    def get(self, request):
        start_date, end_date = get_date_range(request)

        results = (
            Order.objects.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
            )
            .values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )

        serializer = OrderStatusSummarySerializer(list(results), many=True)
        return Response(serializer.data)


class TablePerformanceView(APIView):
    """
    Orders and revenue per table.
    GET /analytics/tables/?start=YYYY-MM-DD&end=YYYY-MM-DD
    """
    permission_classes = [IsAuthenticated, IsAdminOrCashier]

    def get(self, request):
        start_date, end_date = get_date_range(request)

        results = (
            Order.objects.filter(
                status='completed',
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
            )
            .values('table__id', 'table__section', 'table__capacity')
            .annotate(
                order_count=Count('id'),
                total_revenue=Sum('total_amount'),
            )
            .order_by('-total_revenue')
        )

        serializer = TablePerformanceSerializer(list(results), many=True)
        return Response(serializer.data)


class FeedbackSummaryView(APIView):
    """
    Rating distribution and average score.
    GET /analytics/feedback/?start=YYYY-MM-DD&end=YYYY-MM-DD
    """
    permission_classes = [IsAuthenticated, IsAdminOrCashier]

    def get(self, request):
        start_date, end_date = get_date_range(request)

        qs = Feedback.objects.filter(
            order__created_at__date__gte=start_date,
            order__created_at__date__lte=end_date,
        )

        agg = qs.aggregate(
            average_rating=Avg('rating'),
            total_feedback_count=Count('id'),
        )

        rating_dist = {f'rating_{i}': 0 for i in range(1, 6)}
        for row in qs.values('rating').annotate(count=Count('id')):
            key = f"rating_{row['rating']}"
            if key in rating_dist:
                rating_dist[key] = row['count']

        data = {
            'average_rating': round(agg['average_rating'], 2) if agg['average_rating'] else 0.0,
            'total_feedback_count': agg['total_feedback_count'] or 0,
            **rating_dist,
        }

        serializer = FeedbackSummarySerializer(data)
        return Response(serializer.data)


class HourlyOrderPatternView(APIView):
    """
    Order volume and revenue broken down by hour of day.
    GET /analytics/orders/hourly/?start=YYYY-MM-DD&end=YYYY-MM-DD
    """
    permission_classes = [IsAuthenticated, IsAdminOrCashier]

    def get(self, request):
        start_date, end_date = get_date_range(request)

        results = (
            Order.objects.filter(
                status='completed',
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
            )
            .annotate(hour=ExtractHour('created_at'))
            .values('hour')
            .annotate(
                order_count=Count('id'),
                total_revenue=Sum('total_amount'),
            )
            .order_by('hour')
        )

        serializer = HourlyOrderSerializer(list(results), many=True)
        return Response(serializer.data)


class LowStockMenuItemsView(APIView):
    """
    Menu items currently marked as unavailable.
    GET /analytics/menu/unavailable/
    """
    permission_classes = [IsAuthenticated, IsAdminOrCashier]

    def get(self, request):
        items = (
            MenuItem.objects.filter(availability=False)
            .select_related('category')
            .values('id', 'name', 'price', 'category__name')
        )
        return Response(list(items))