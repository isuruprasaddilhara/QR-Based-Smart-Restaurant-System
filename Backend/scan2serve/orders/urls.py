from django.urls import path
from .views import (
    OrderListCreateView,
    OrderDetailView,
    OrderStatusUpdateView,
    FeedbackCreateView,
    FeedbackDetailView,
    request_bill_view,
)

urlpatterns = [
    path('', OrderListCreateView.as_view(), name='order-list-create'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('<int:pk>/status/', OrderStatusUpdateView.as_view(), name='order-status-update'),
    path('<int:order_id>/request-bill/', request_bill_view, name='order-request-bill'),
    path('<int:pk>/feedback/', FeedbackCreateView.as_view(), name='feedback-create'),
    path('<int:pk>/feedback/detail/', FeedbackDetailView.as_view(), name='feedback-detail'),
]