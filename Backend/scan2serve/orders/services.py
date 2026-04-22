from .models import Order
import requests

def request_bill(order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        raise ValueError(f"Order {order_id} does not exist.")

    if order.status != 'served':
        raise ValueError(
            f"Bill can only be requested for orders with status 'served'. "
            f"Current status: '{order.status}'."
        )

    if order.status == 'requested':
        raise ValueError("Bill already requested.")

    order.status = 'requested'
    order.save(update_fields=['status'])

    return order


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
    # headers = {
    #     'Content-Type': 'application/json',
    #     'X-ESP32-Token': ESP32_SECRET_TOKEN,
    # }
    payload = {'frequency': frequency, 'duration': duration_ms}

    try:
        response = requests.post(url, json=payload, timeout=3) #headers=headers,
        response.raise_for_status()
    except requests.RequestException as exc:
        # Log but don't crash the order creation flow.
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Could not reach kitchen ESP32 at %s: %s", esp32_ip, exc)
