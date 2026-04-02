import uuid
import qrcode
from io import BytesIO
from .models import Table

def create_table_with_qr (section: str = None, capacity: int = 2) -> Table:
    token = str(uuid.uuid4())
    table = Table.objects.create(qr_code=token, status=False, section=section, capacity=capacity)
    return table

def build_qr_image(table: Table, base_url: str = "https://yourapp.com/menu") -> BytesIO:
    qr_url = f"{base_url}?table_no={table.id}&token={table.qr_code}"  # both id and token in URL

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer