import uuid
import qrcode
from io import BytesIO
from .models import Table

def create_table_with_qr ( table_number: int, section: str = None, capacity: int = 2) -> Table:
    token = str(uuid.uuid4())
    table = Table.objects.create(table_number=table_number, qr_code=token, status=False, section=section, capacity=capacity)
    return table

def build_qr_image(table: Table, base_url: str = "https://yourapp.com/menu") -> BytesIO:
    qr_url = f"{base_url}?table_no={table.table_number}&token={table.qr_code}"  # both table_number and token in URL

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer


# # ── Helper used by orders/signals.py ──────────────────────────────────────────

# def trigger_kitchen_buzzer(esp32_ip: str, frequency: int = 2500, duration_ms: int = 2000):
#     """
#     Send a POST request to the ESP32 to sound the kitchen buzzer.
#     Call this from the order-created signal (see orders/signals.py).

#     Args:
#         esp32_ip:    IP address of the kitchen ESP32 (e.g. "192.168.1.101").
#         frequency:   Buzzer tone in Hz.
#         duration_ms: How long to sound the buzzer in milliseconds.
#     """
#     url = f"http://{esp32_ip}/buzzer"
#     headers = {
#         'Content-Type': 'application/json',
#         'X-ESP32-Token': ESP32_SECRET_TOKEN,
#     }
#     payload = {'frequency': frequency, 'duration': duration_ms}

#     try:
#         response = requests.post(url, json=payload, headers=headers, timeout=3)
#         response.raise_for_status()
#     except requests.RequestException as exc:
#         # Log but don't crash the order creation flow.
#         import logging
#         logger = logging.getLogger(__name__)
#         logger.warning("Could not reach kitchen ESP32 at %s: %s", esp32_ip, exc)
