from django.urls import path
from . import views

urlpatterns = [
    path('',                             views.table_list,          name='table-list'),
    path('<int:pk>/',                   views.table_detail,        name='table-detail'),
    path('<int:pk>/toggle-status/',     views.toggle_table_status, name='table-toggle-status'),
    path('<int:pk>/download-qr/',       views.download_qr,         name='table-download-qr'),
    # NEW: Called by the ESP32 IR sensor
    path('<int:pk>/ir-status/',          views.ir_status_update,    name='table-ir-status'),
]