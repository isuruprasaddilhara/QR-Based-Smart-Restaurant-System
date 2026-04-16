from django.http import FileResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Table
from .serializers import TableSerializer
from .services import create_table_with_qr, build_qr_image
from users.permissions import IsAdmin, IsKitchen, IsCashier, IsAdminOrReadOnly
from django.conf import settings
from rest_framework.permissions import AllowAny

@api_view(['GET', 'POST'])
@permission_classes([IsAdmin | IsCashier])  
def table_list(request):
    if request.method == 'GET':
        tables = Table.objects.all()
        serializer = TableSerializer(tables, many=True, context={'request': request})
        return Response(serializer.data)

    if request.method == 'POST':
        table_number = request.data.get('table_number')
        section = request.data.get('section', None)
        capacity = request.data.get('capacity', 2)
        table = create_table_with_qr(table_number=table_number, section=section, capacity=capacity)
        serializer = TableSerializer(table, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAdmin | IsCashier])  
def table_detail(request, pk):
    try:
        table = Table.objects.get(pk=pk)
    except Table.DoesNotExist:
        return Response({'error': 'Table not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = TableSerializer(table, context={'request': request})
        return Response(serializer.data)

    if request.method == 'PATCH':
        serializer = TableSerializer(table, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        table.delete()
        return Response({'message': 'Table deleted.'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['PATCH'])
def toggle_table_status(request, pk):
    try:
        table = Table.objects.get(pk=pk)
    except Table.DoesNotExist:
        return Response({'error': 'Table not found.'}, status=status.HTTP_404_NOT_FOUND)

    table.status = not table.status
    table.save()
    return Response({
        'id': table.id,
        'status': table.status,
        'message': f"Table is now {'occupied' if table.status else 'available'}."
    })


@api_view(['GET'])
@permission_classes([IsAdmin | IsCashier]) 
def download_qr(request, pk):
    try:
        table = Table.objects.get(pk=pk)
    except Table.DoesNotExist:
        return Response({'error': 'Table not found.'}, status=status.HTTP_404_NOT_FOUND)

    base_url = request.query_params.get('base_url', 'https://yourapp.com/menu')
    buffer = build_qr_image(table, base_url=base_url)  # pass full table object

    response = FileResponse(buffer, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="table_{table.id}_qr.png"'
    return response


# ── NEW: IR sensor endpoint ────────────────────────────────────────────────────

ESP32_SECRET_TOKEN = getattr(settings, 'ESP32_SECRET_TOKEN', 'CHANGE_ME_SECRET_TOKEN')


@api_view(['POST'])
@permission_classes([AllowAny])   # Auth is done via the shared secret token below.
def ir_status_update(request, pk):
    """
    POST /api/tables/<pk>/ir-status/
    Called by the ESP32 whenever the IR sensor state changes.

    Headers:
        X-ESP32-Token: <ESP32_SECRET_TOKEN from settings>

    Body (JSON):
        { "occupied": true }   or   { "occupied": false }

    Effect:
        Updates Table.status  (True = occupied, False = available).
    """
    # Verify the shared secret so only the ESP32 can call this.
    token = request.headers.get('X-ESP32-Token', '')
    if token != ESP32_SECRET_TOKEN:
        return Response({'error': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        table = Table.objects.get(pk=pk)
    except Table.DoesNotExist:
        return Response({'error': 'Table not found.'}, status=status.HTTP_404_NOT_FOUND)

    occupied = request.data.get('occupied')
    if occupied is None:
        return Response(
            {'error': '`occupied` (boolean) is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    table.status = bool(occupied)
    table.save(update_fields=['status'])

    return Response({
        'id': table.id,
        'status': table.status,
        'message': f"Table is now {'occupied' if table.status else 'available'}.",
    })


# ── Helper used by orders/signals.py ──────────────────────────────────────────

def trigger_kitchen_buzzer(esp32_ip: str, frequency: int = 2500, duration_ms: int = 2000):
    """
    Send a POST request to the ESP32 to sound the kitchen buzzer.
    Call this from the order-created signal (see orders/signals.py).

    Args:
        esp32_ip:    IP address of the kitchen ESP32 (e.g. "192.168.1.101").
        frequency:   Buzzer tone in Hz.
        duration_ms: How long to sound the buzzer in milliseconds.
    """
    url = f"http://{esp32_ip}/buzzer"
    headers = {
        'Content-Type': 'application/json',
        'X-ESP32-Token': ESP32_SECRET_TOKEN,
    }
    payload = {'frequency': frequency, 'duration': duration_ms}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=3)
        response.raise_for_status()
    except requests.RequestException as exc:
        # Log but don't crash the order creation flow.
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Could not reach kitchen ESP32 at %s: %s", esp32_ip, exc)
