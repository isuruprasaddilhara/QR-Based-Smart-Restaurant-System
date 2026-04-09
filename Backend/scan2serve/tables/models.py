from django.db import models

class Table(models.Model):
    table_number = models.PositiveIntegerField(unique=True, null=True, blank=True)
    qr_code = models.CharField(max_length=255, unique=True)
    status = models.BooleanField(default=False) #true = occupied, false = available
    section = models.CharField(max_length=100, blank=True, null=True)
    capacity = models.PositiveIntegerField(default=2)

    def __str__(self):
        return f"Table {self.table_number} - Section: {self.section or 'N/A'} (Capacity: {self.capacity})"