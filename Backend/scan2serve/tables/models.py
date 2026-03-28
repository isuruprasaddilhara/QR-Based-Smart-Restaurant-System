from django.db import models

class Table(models.Model):
    qr_code = models.CharField(max_length=255, unique=True)
    status = models.BooleanField(default=False)

    def __str__(self):
        return f"Table {self.id}"