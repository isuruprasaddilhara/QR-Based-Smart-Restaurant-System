from .models import Order
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

    order.status = 'completed'
    order.save()
    return order