from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from .models import Order, Feedback
from .serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    OrderStatusSerializer,
    FeedbackSerializer,
)
from .services import request_bill


class OrderListCreateView(generics.ListCreateAPIView):
    """List all orders or create a new order with items."""
    queryset = Order.objects.prefetch_related('items__menu_item', 'feedback').all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific order."""
    queryset = Order.objects.prefetch_related('items__menu_item', 'feedback').all()
    serializer_class = OrderSerializer


class OrderStatusUpdateView(APIView):
    """
    PATCH /orders/<pk>/status/
    Update only the status of an order.
    Body: { "status": "preparing" }
    """
    def patch(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        serializer = OrderStatusSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeedbackCreateView(generics.CreateAPIView):
    """POST /orders/<pk>/feedback/ — Submit feedback for a completed order."""
    serializer_class = FeedbackSerializer

    def perform_create(self, serializer):
        order = get_object_or_404(Order, pk=self.kwargs['pk'])

        if hasattr(order, 'feedback'):
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Feedback already exists for this order.")

        serializer.save(order=order)


class FeedbackDetailView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /orders/<pk>/feedback/detail/ — Retrieve or update feedback."""
    serializer_class = FeedbackSerializer

    def get_object(self):
        return get_object_or_404(Feedback, order__pk=self.kwargs['pk'])


@api_view(['POST'])
def request_bill_view(request, order_id):
    """
    POST /orders/<order_id>/request-bill/
    Marks the order as completed via the service layer.
    """
    try:
        order = request_bill(order_id)
        return Response({
            'message': 'Bill requested successfully.',
            'order_id': order.id,
            'total_amount': order.total_amount,
            'status': order.status,
        })
    except ValueError as e:
        return Response({'error': str(e)}, status=400)