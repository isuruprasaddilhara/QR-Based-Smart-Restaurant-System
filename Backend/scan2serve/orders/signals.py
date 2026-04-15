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


# ── Sound the kitchen buzzer when a new order is created ─────────────────────

@receiver(post_save, sender=Order)
def notify_kitchen_on_new_order(sender, instance, created, **kwargs):
    """
    When a new Order is saved for the first time, fire an HTTP request to the
    kitchen ESP32 so the buzzer alerts kitchen staff.

    Settings required in settings.py:
        KITCHEN_ESP32_IP    = "192.168.1.101"   # IP of the kitchen ESP32
        ESP32_SECRET_TOKEN  = "CHANGE_ME_SECRET_TOKEN"
    """
    if not created:
        return  # Only trigger on brand-new orders, not updates.

    esp32_ip = getattr(settings, 'KITCHEN_ESP32_IP', None)
    if not esp32_ip:
        logger.warning(
            "KITCHEN_ESP32_IP is not set in settings. "
            "Kitchen buzzer will not be triggered."
        )
        return

    # Import here to avoid circular imports (tables app ↔ orders app).
    from tables.views import trigger_kitchen_buzzer

    logger.info("New order #%s created — triggering kitchen buzzer at %s", instance.pk, esp32_ip)
    trigger_kitchen_buzzer(esp32_ip, frequency=2500, duration_ms=2000)
