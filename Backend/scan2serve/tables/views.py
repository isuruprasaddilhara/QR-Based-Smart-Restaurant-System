from django.http import FileResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Table
from .serializers import TableSerializer
from .services import create_table_with_qr, build_qr_image
from users.permissions import IsAdmin, IsKitchen, IsCashier, IsAdminOrReadOnly



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