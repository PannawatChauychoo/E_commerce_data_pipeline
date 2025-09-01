# pyright: reportMissingImports=false
from rest_framework import serializers

from .models import Cust1, Cust2, Products, SimulationRun, Transactions


class SimulationInputSerializer(serializers.Serializer):
    # Accept both "2025-01-01" and "20250101"
    start_date = serializers.DateField(input_formats=["%Y-%m-%d", "%Y%m%d"])
    max_steps = serializers.IntegerField(min_value=1, max_value=100000)
    n_customers1 = serializers.IntegerField(min_value=0)
    n_customers2 = serializers.IntegerField(min_value=0)
    n_products_per_category = serializers.IntegerField(min_value=1, max_value=100000)

    def validate(self, data):
        # Cross-field rule: need at least one customer overall
        if data["n_customers1"] + data["n_customers2"] <= 0:
            raise serializers.ValidationError("At least one customer is required.")

        if data["n_products_per_category"] <= 0:
            raise serializers.ValidationError("Need more than 1 product per cateogory.")
        return data


class TransactionSerializer(serializers.ModelSerializer):
    # if your model class is named FctTransactions, import and use that instead
    order_value = serializers.SerializerMethodField()

    class Meta:
        model = Transactions
        # only expose the fields your front end needs:
        fields = (
            "transaction_id",
            "date_purchased",
            "category",
            "unit_price",
            "quantity",
            "order_value",
        )

    def get_order_value(self, obj):
        # compute on-the-fly instead of storing in the DB
        return obj.unit_price * obj.quantity


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = (
            "product_id",  # adjust to your actual column names
            "category",
            "unit_price",
            "stock",
            "lead_days",
            "ordering_cost",
            "holding_cost_per_unit",
            "eoq",
        )


class Cust1Serializer(serializers.ModelSerializer):
    class Meta:
        model = Cust1
        fields = (
            "unique_id",
            "age",
            "gender",
            "city_category",
            "stay_in_current_city_years",
            "marital_status",
            "visit_prob",
        )


class Cust2Serializer(serializers.ModelSerializer):
    class Meta:
        model = Cust2
        fields = (
            "unique_id",
            "branch",
            "city",
            "gender",
        )
