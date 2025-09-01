from django.urls import path

from .views import (Cust1ListView, Cust2ListView, ProductListView,
                    RunProgressView, StartSimulationView, TransactionListView)

urlpatterns = [
    path("transactions/", TransactionListView.as_view(), name="transactions-list"),
    path("simulate/", StartSimulationView.as_view(), name="simulate"),
    path("simulate/<str:run_id>", RunProgressView.as_view(), name="simulate-progress"),
    path("cust1/", Cust1ListView.as_view(), name="cust1-list"),
    path("cust2/", Cust2ListView.as_view(), name="cust2-list"),
    path("products/", ProductListView.as_view(), name="product-list"),
]
