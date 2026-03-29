from django.shortcuts import render
from rest_framework import viewsets
from .models import MenuCategory, MenuItem
from .serializers import MenuSerializer, MenuCategorySerializer
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS, AllowAny
from rest_framework.response import Response
from rest_framework import status
from users.permissions import IsAdmin, IsCustomer

class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuSerializer

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated & IsAdmin]
        return [permission() for permission in permission_classes]



class MenuCategoryViewSet(viewsets.ModelViewSet):
    queryset = MenuCategory.objects.all()
    serializer_class = MenuCategorySerializer

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated & IsAdmin]
        return [permission() for permission in permission_classes]

