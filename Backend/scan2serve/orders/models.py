from django.db import models
from users.models import User
from tables.models import Table
from menu.models import MenuItem
from django.utils import timezone

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('served', 'Served'),
        ('requested', 'Requested'),
        ('completed', 'Completed'),
    )

    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True, blank=True)
    guest_token = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    special_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    preparing_at = models.DateTimeField(null=True, blank=True)
    served_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order {self.id}"

    def save(self, *args, **kwargs):
        if self.pk:
            old = Order.objects.get(pk=self.pk)

            if old.status != self.status:
                if self.status == 'preparing' and not self.preparing_at:
                    self.preparing_at = timezone.now()

                if self.status == 'served' and not self.served_at:
                    self.served_at = timezone.now()

                if self.status == 'completed' and not self.completed_at:
                    self.completed_at = timezone.now()

        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
   
    def __str__(self):
        return f"{self.menu_item.name} x {self.quantity}"
    


class Feedback(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='feedback')
    rating = models.IntegerField()
    comment = models.TextField(blank=True)

    def __str__(self):
        return f"Feedback for Order {self.order.id}"