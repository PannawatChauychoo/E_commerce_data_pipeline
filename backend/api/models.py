import uuid

from django.contrib.auth.models import User
from django.db import models


class SimulationRun(models.Model):
    """Track each analysis execution"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=[
            ("running", "Running"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="running",
    )
    input_parameters = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class Cust1(models.Model):
    unique_id = models.IntegerField(primary_key=True)
    age = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    city_category = models.CharField(max_length=20, blank=True, null=True)
    stay_in_current_city_years = models.CharField(max_length=10, blank=True, null=True)
    marital_status = models.CharField(max_length=10, blank=True, null=True)
    segment_id = models.IntegerField(blank=True, null=True)
    visit_prob = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "cust1"


class Cust2(models.Model):
    unique_id = models.IntegerField(primary_key=True)
    branch = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    customer_type = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    payment_method = models.CharField(max_length=20, blank=True, null=True)
    segment_id = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "cust2"


class CustomersLookup(models.Model):
    customer_id = models.AutoField(primary_key=True)
    external_id = models.IntegerField()
    cust_type = models.CharField(max_length=10)
    segment_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "customers_lookup"
        unique_together = (("external_id", "cust_type", "segment_id"),)


class Products(models.Model):
    product_id = models.IntegerField(primary_key=True)
    category = models.CharField(max_length=100)
    unit_price = models.FloatField()
    stock = models.IntegerField(blank=True, null=True)
    lead_days = models.IntegerField(blank=True, null=True)
    ordering_cost = models.FloatField(blank=True, null=True)
    holding_cost_per_unit = models.FloatField(blank=True, null=True)
    eoq = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "products"


class Transactions(models.Model):
    transaction_id = models.AutoField(primary_key=True)
    unique = models.ForeignKey(
        CustomersLookup,
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name="transactions",
    )
    product = models.ForeignKey(
        Products, models.DO_NOTHING, blank=True, null=True, related_name="transactions"
    )
    unit_price = models.FloatField(blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    date_purchased = models.DateField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    order_value = models.FloatField(blank=True, null=True)

    # Add computed property for order_value
    def save(self, *args, **kwargs):
        # Auto-calculate order_value when saving
        if self.unit_price and self.quantity:
            self.order_value = self.unit_price * self.quantity
        else:
            self.order_value = 0
        super().save(*args, **kwargs)

    class Meta:
        managed = False
        db_table = "transactions"
