from django.urls import path
from .views import (
    DashboardSummaryView,
    RevenueAnalyticsView,
    TopMenuItemsView,
    CategoryRevenueView,
    OrderStatusSummaryView,
    TablePerformanceView,
    FeedbackSummaryView,
    HourlyOrderPatternView,
    LowStockMenuItemsView,
)

urlpatterns = [
    # Dashboard
    path('dashboard/', DashboardSummaryView.as_view(), name='analytics-dashboard'),

    # Revenue
    path('revenue/', RevenueAnalyticsView.as_view(), name='analytics-revenue'),

    # Menu
    path('menu/top-items/', TopMenuItemsView.as_view(), name='analytics-top-items'),
    path('menu/categories/', CategoryRevenueView.as_view(), name='analytics-categories'),
    path('menu/unavailable/', LowStockMenuItemsView.as_view(), name='analytics-unavailable'),

    # Orders
    path('orders/status/', OrderStatusSummaryView.as_view(), name='analytics-order-status'),
    path('orders/hourly/', HourlyOrderPatternView.as_view(), name='analytics-hourly'),

    # Tables
    path('tables/', TablePerformanceView.as_view(), name='analytics-tables'),

    # Feedback
    path('feedback/', FeedbackSummaryView.as_view(), name='analytics-feedback'),
]