from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import OrderItem


@receiver(post_save, sender=OrderItem)
@receiver(post_delete, sender=OrderItem)
def update_order_total(sender, instance, **kwargs):
    """Automatically update Order.total_amount whenever an OrderItem changes."""
    order = instance.order
    order.total_amount = order.calculate_total()
    order.save(update_fields=['total_amount'])