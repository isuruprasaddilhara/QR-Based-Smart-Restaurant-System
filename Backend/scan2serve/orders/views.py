from rest_framework import generics, status
from rest_framework.views import APIView
from users.permissions import IsAdmin, IsKitchen, IsCashier, IsCustomer, IsAdminOrReadOnly, HasAnyRole
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from .models import Order, Feedback
from .serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    OrderStatusSerializer,
    FeedbackSerializer,
)
from .services import request_bill
from .bill_generator import generate_bill_pdf, generate_thermal_pdf
from django.http import HttpResponse
from django.core.mail import EmailMessage

def get_order_for_request(request, pk):
    """
    Fetch an order and verify the requester is allowed to access it.
    - Authenticated users: must own the order or be staff/admin
    - Guests: must supply matching X-Guest-Token header
    """
    order = get_object_or_404(Order, pk=pk)

    if request.user.is_authenticated:
        if request.user.is_staff or hasattr(request.user, 'role') and request.user.role != 'customer':
            return order  # kitchen, cashier, admin bypass
        if order.user == request.user:
            return order
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("You do not have access to this order.")

    # Guest access via token
    guest_token = request.headers.get('X-Guest-Token')
    if guest_token and guest_token == order.guest_token:
        return order

    from rest_framework.exceptions import PermissionDenied
    raise PermissionDenied("You do not have access to this order.")

    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny]  # guests can create orders
        return [IsAdmin | IsKitchen | IsCashier]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        guest_token = None if user else secrets.token_urlsafe(32)

        serializer.save(user=user, guest_token=guest_token)

class OrderListCreateView(generics.ListCreateAPIView):
    """List all orders or create a new order with items."""
    queryset = Order.objects.prefetch_related('items__menu_item', 'feedback').all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer

    def get_permissions(self):
        if self.action == 'create':          # POST
            # guests (anon) + customers can submit orders
            return [AllowAnonymous() | IsCustomer()]

        if self.action in ('update', 'partial_update', 'retrieve', 'list'):  # GET + PUT/PATCH
            # staff roles only
            return [IsAdmin() | IsKitchen() | IsCashier()]

        if self.action == 'destroy':         # DELETE
            return [IsAdmin()]               # lock down deletes to admin only

        return [IsAdmin()]


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific order."""
    queryset = Order.objects.prefetch_related('items__menu_item', 'feedback').all()
    serializer_class = OrderSerializer
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]  # access controlled manually in get_object
        return [IsAdmin() | IsCashier()]

    def get_object(self):
        return get_order_for_request(self.request, self.kwargs['pk'])


class OrderStatusUpdateView(APIView):
    
    permission_classes = [IsAdmin | IsKitchen | IsCashier]
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
    permission_classes = [AllowAny]
    serializer_class = FeedbackSerializer

    def perform_create(self, serializer):
        order = get_object_or_404(Order, pk=self.kwargs['pk'])

        if hasattr(order, 'feedback'):
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Feedback already exists for this order.")

        serializer.save(order=order)

class FeedbackListView(generics.ListAPIView):
    """GET /feedbacks/ — List all feedbacks."""
    serializer_class = FeedbackSerializer
    queryset = Feedback.objects.select_related('order').all()


class FeedbackDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [AllowAny]
    """GET/PATCH /orders/<pk>/feedback/detail/ — Retrieve or update feedback."""
    serializer_class = FeedbackSerializer

    def get_object(self):
        return get_object_or_404(Feedback, order__pk=self.kwargs['pk'])


@api_view(['POST'])
@permission_classes([AllowAny])
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



# ── Bill Views ─────────────────────────────────────────────────────────────────

def _mark_order_completed(order):
    """Set order status to completed if not already, and save."""
    if order.status != 'completed':
        order.status = 'completed'
        order.save(update_fields=['status'])

@api_view(['POST'])
@permission_classes([AllowAny])
def bill_soft_copy_view(request, order_id):
    """
    POST /orders/<order_id>/bill/soft/
    Generate the bill PDF and email it to the customer.

    Body (JSON):
        { "email": "customer@example.com" }

    Access: same rules as order detail — owner, guest token, or staff.
    """
    order = get_order_for_request(request, order_id)

    email_to = request.data.get('email', '').strip()
    if not email_to:
        return Response(
            {'error': 'An email address is required.'},
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
    from_email = getattr(restaurant, 'email', None) if restaurant else None
    from_email = from_email or 'noreply@scan2serve.app'
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
@permission_classes([AllowAny])
def bill_hard_copy_view(request, order_id):
    """
    GET /orders/<order_id>/bill/print/
    Returns the bill PDF inline so the browser print dialog opens automatically.

    Frontend usage:
        window.open(`/api/orders/${orderId}/bill/print/`, '_blank')
        // the new tab loads the PDF and the user hits Ctrl+P (or auto-print via JS)

    Access: same rules as order detail — owner, guest token, or staff.
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