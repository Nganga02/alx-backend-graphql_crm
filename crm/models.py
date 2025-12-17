import uuid
from django.db import models


# Create your models here.
class Customer(models.Model):
    customer_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True
    )

    name = models.CharField(
        max_length=100,
        blank=False
    )

    email = models.EmailField(
        blank=False,
        unique=True
    )

    phone= models.CharField(
        blank=True
    )

    def __str__(self):
        return f'{self.name}'

class Product(models.Model):
    product_id= models.UUIDField(
        primary_key=True,
        default= uuid.uuid4,
        editable=False,
        db_index=True
    )

    name= models.CharField(
        max_length=100,
        blank=False
    )
    
    price= models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    stock= models.PositiveIntegerField(
        default=0
    )

    def __str__(self):
        return f'{self.name}'

class Order(models.Model):
    order_id= models.UUIDField(
        primary_key=True,
        default= uuid.uuid4,
        editable=False,
        db_index=True
    )

    customer= models.ForeignKey(
        Customer,
        on_delete=models.DO_NOTHING,
        related_name='purchases'
    )

    product= models.ManyToManyField(
        Product,
        related_name= 'dispatched_orders'
    )
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(name):
        return f'{name}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.products.exists():
            self.total_amount = sum(p.price for p in self.products.all())
            super().save(update_fields=['total_amount'])