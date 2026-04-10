from django.shortcuts import render
from rest_framework import viewsets
from .models import MenuCategory, MenuItem
from .serializers import MenuSerializer, MenuCategorySerializer
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS, AllowAny
from rest_framework.response import Response
from rest_framework import status
from users.permissions import IsAdminOrCashierOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView

class MenuItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrCashierOrReadOnly]
    queryset = MenuItem.objects.select_related('category').all()
    serializer_class = MenuSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_context(self):
        # ensures 'request' is always passed into serializer
        # so get_image_url() can build the full absolute URL
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class MenuCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrCashierOrReadOnly]
    queryset = MenuCategory.objects.all()
    serializer_class = MenuCategorySerializer



