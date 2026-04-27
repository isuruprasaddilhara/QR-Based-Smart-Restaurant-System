import secrets
from django.conf import settings
import requests
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsAdmin, IsKitchen, IsCashier, IsCustomer,IsStaff

from .bill_generator import generate_bill_pdf, generate_thermal_pdf
from .models import Order, Feedback
from .serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    OrderStatusSerializer,
    FeedbackSerializer,
    CashierBillRequestSerializer
)
from .services import request_bill
from scan2serve.throttles import OrderCreateThrottle

# ── Helpers / Mixins ───────────────────────────────────────────────────────────

def get_order_for_request(request, pk):
    """
    Fetch an order and verify the requester is allowed to access it.
    - Authenticated users: must own the order or be staff / non-customer role.
    - Guests: must supply a matching X-Guest-Token header.
    """
    order = get_object_or_404(Order, pk=pk)

    if request.user.is_authenticated:
        # Staff, admin, kitchen, cashier roles bypass ownership check.
        if request.user.is_staff or (
            hasattr(request.user, 'role') and request.user.role != 'customer'
        ):
            return order
        if order.user == request.user:
            return order
        raise PermissionDenied("You do not have access to this order.")

    # Guest access via token
    guest_token = request.headers.get('X-Guest-Token')
    if guest_token and guest_token == order.guest_token:
        return order

    raise PermissionDenied("You do not have access to this order.")


class OrderAccessMixin:
    """Convenience mixin so class-based views can call self.get_order(pk)."""

    def get_order(self, pk):
        return get_order_for_request(self.request, pk)


def _mark_order_completed(order):
    """
    Set order status to completed if not already.
    Uses a queryset update to avoid a race condition, then syncs the
    in-memory object so callers don't need to re-fetch.
    """
    if order.status != 'completed':
        Order.objects.filter(pk=order.pk).update(status='completed')
        order.status = 'completed'


# ── Order Views ────────────────────────────────────────────────────────────────

class OrderListCreateView(generics.ListCreateAPIView):
    """List all orders (staff only) or create a new order with items."""
    throttle_classes = [OrderCreateThrottle]
    queryset = (
        Order.objects
        .select_related('user', 'table')
        .prefetch_related('items__menu_item', 'feedback')
        .all()
    )

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            # Both guests (AllowAny) and authenticated customers may create orders.
            return [AllowAny()]
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [(IsAdmin | IsKitchen | IsCashier)()]
        return [IsAdmin()]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        guest_token = None if user else secrets.token_urlsafe(32)
        serializer.save(user=user, guest_token=guest_token)
        esp32_ip = getattr(settings, 'KITCHEN_ESP32_IP', None)
        from orders.services import trigger_kitchen_buzzer
        #logger.info("New order #%s created — triggering kitchen buzzer at %s", instance.pk, esp32_ip)
        trigger_kitchen_buzzer(esp32_ip, frequency=2500, duration_ms=2000)


class OrderDetailView(OrderAccessMixin, generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific order."""

    queryset = (
        Order.objects
        .select_related('user', 'table__restaurant')
        .prefetch_related('items__menu_item', 'feedback')
        .all()
    )
    serializer_class = OrderSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            # Ownership / guest-token check is enforced in get_object().
            return [AllowAny()]
        return [(IsAdmin | IsCashier | IsKitchen)()]

    def get_object(self):
        return self.get_order(self.kwargs['pk'])


class OrderStatusUpdateView(APIView):
    """PATCH /orders/<pk>/status/ — Update only the status of an order."""

    permission_classes = [IsStaff]

    def patch(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        serializer = OrderStatusSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Feedback Views ─────────────────────────────────────────────────────────────

class FeedbackCreateView(OrderAccessMixin, generics.CreateAPIView):
    """POST /orders/<pk>/feedback/ — Submit feedback for a completed order."""

    serializer_class = FeedbackSerializer

    def perform_create(self, serializer):
        # Re-use access control: owner, guest token, or staff only.
        order = self.get_order(self.kwargs['pk'])

        if hasattr(order, 'feedback'):
            raise ValidationError("Feedback already exists for this order.")

        serializer.save(order=order)


class FeedbackListView(generics.ListAPIView):
    """GET /feedbacks/ — List all feedbacks (staff use)."""
    permission_classes = [IsStaff]
    serializer_class = FeedbackSerializer
    queryset = Feedback.objects.select_related('order').all()


class FeedbackDetailView(OrderAccessMixin, generics.RetrieveUpdateAPIView):
    """GET/PATCH /orders/<pk>/feedback/detail/ — Retrieve or update feedback."""

    permission_classes = [IsStaff]
    serializer_class = FeedbackSerializer

    def get_object(self):
        # Validate the requester can access the parent order first.
        self.get_order(self.kwargs['pk'])
        return get_object_or_404(Feedback, order__pk=self.kwargs['pk'])


# ── Bill / Request-Bill Views ──────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def request_bill_view(request, order_id):
    """
    POST /orders/<order_id>/request-bill/
    Marks the order as bill-requested via the service layer.
    """
    try:
        order = request_bill(order_id)
        return Response({
            'message': 'Bill requested successfully.',
            'order_id': order.id,
            'total_amount': order.total_amount,
            'status': order.status,
        })
    except ValueError as exc:
        return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

class BillRequestedOrdersView(generics.ListAPIView):
    serializer_class = CashierBillRequestSerializer

    def get_queryset(self):
        return (
            Order.objects
            .filter(status='requested')
            .select_related('table', 'user')
            .prefetch_related('items__menu_item')
            .order_by('-created_at')
        )


@api_view(['POST'])
@permission_classes([IsCashier])
def bill_soft_copy_view(request, order_id):
    """
    POST /orders/<order_id>/bill/soft/
    Generate the bill PDF and e-mail it to the customer.

    Body (JSON):
        { "email": "customer@example.com" }

    Access: owner, guest token, or staff.
    """
    order = get_order_for_request(request, order_id)

    email_to = request.data.get('email', '').strip()
    if not email_to:
        return Response(
            {'error': 'An email address is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate e-mail format before attempting anything expensive.
    try:
        validate_email(email_to)
    except DjangoValidationError:
        return Response(
            {'error': 'Invalid email address.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        _mark_order_completed(order)
        pdf_bytes = generate_bill_pdf(order)
    except Exception as exc:
        return Response(
            {'error': 'Could not generate bill.', 'detail': str(exc)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    restaurant = getattr(order.table, 'restaurant', None)
    rest_name  = getattr(restaurant, 'name', 'Scan2Serve Restaurant') if restaurant else 'Scan2Serve Restaurant'
    from_email = (getattr(restaurant, 'email', None) if restaurant else None) or 'scan2serve.email@gmail.com'
    tbl_number = getattr(order.table, 'number', getattr(order.table, 'table_number', order.table.pk))

    try:
        mail = EmailMessage(
            subject=f"Your Bill from {rest_name} – Table {tbl_number}",
            body=(
                f"Dear Guest,\n\n"
                f"Thank you for dining at {rest_name}!\n"
                f"Your bill for Table {tbl_number} is attached.\n\n"
                f"Total: LKR {order.total_amount:.2f}\n\n"
                f"We hope to see you again soon.\n\n"
                f"– {rest_name} Team\nPowered by Scan2Serve"
            ),
            from_email=from_email,
            to=[email_to],
        )
        mail.attach(f"bill_order_{order_id}.pdf", pdf_bytes, 'application/pdf')
        mail.send(fail_silently=False)
    except Exception as exc:
        return Response(
            {'error': 'Bill generated but email delivery failed.', 'detail': str(exc)},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    return Response({
        'message': f'Bill sent to {email_to}.',
        'order_id': order_id,
        'total_amount': str(order.total_amount),
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsCashier])
def bill_hard_copy_view(request, order_id):
    """
    GET /orders/<order_id>/bill/print/
    Returns the bill PDF inline so the browser print dialog opens automatically.

    Frontend usage:
        window.open(`/api/orders/${orderId}/bill/print/`, '_blank')

    Access: owner, guest token, or staff.
    """
    order = get_order_for_request(request, order_id)

    try:
        _mark_order_completed(order)
        pdf_bytes = generate_thermal_pdf(order)
    except Exception as exc:
        return Response(
            {'error': 'Could not generate bill.', 'detail': str(exc)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="bill_order_{order_id}.pdf"'
    response['Content-Length'] = len(pdf_bytes)
    return response