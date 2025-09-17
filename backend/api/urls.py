import os
from django.urls import path

from .views import (ContinuityCheckView, RunProgressView, SimulationPreviewView, StartSimulationView, FileListView, FileDownloadView)

# Cache-only URLs (simulation endpoints that work without database)
cache_only_urls = [
    path("simulate/", StartSimulationView.as_view(), name="simulate"),
    path("simulate/can-continue/", ContinuityCheckView.as_view(), name="can-continue"),
    path("simulate/preview/", SimulationPreviewView.as_view(), name="simulate-preview"),
    path("simulate/<str:run_id>", RunProgressView.as_view(), name="simulate-progress"),
    path("files/list/", FileListView.as_view(), name="files-list"),
    path("files/download/<path:file_path>/", FileDownloadView.as_view(), name="files-download"),
]

# Database-dependent URLs (only enabled when database is available)
if not os.getenv("DISABLE_DATABASE", "False").lower() == "true":
    from .views import (Cust1ListView, Cust2ListView, ProductListView, TransactionListView)

    database_urls = [
        path("transactions/", TransactionListView.as_view(), name="transactions-list"),
        path("cust1/", Cust1ListView.as_view(), name="cust1-list"),
        path("cust2/", Cust2ListView.as_view(), name="cust2-list"),
        path("products/", ProductListView.as_view(), name="product-list"),
    ]
    urlpatterns = cache_only_urls + database_urls
else:
    urlpatterns = cache_only_urls
