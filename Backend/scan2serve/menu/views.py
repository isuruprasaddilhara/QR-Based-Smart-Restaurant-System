from django.shortcuts import render
from rest_framework import viewsets
from .models import MenuCategory, MenuItem
from .serializers import MenuSerializer, MenuCategorySerializer
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS, AllowAny
from rest_framework.response import Response
from rest_framework import status
from users.permissions import IsAdminOrReadOnly

class MenuItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = MenuItem.objects.all()
    serializer_class = MenuSerializer


class MenuCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = MenuCategory.objects.all()
    serializer_class = MenuCategorySerializer

 

