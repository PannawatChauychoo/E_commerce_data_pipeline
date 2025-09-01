# pyright: reportMissingImports=false
import threading
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import timedelta
from threading import Lock
from typing import Any, Dict, List

from django.db.models import Case, DecimalField, F, Sum, When
from django.http import Http404, JsonResponse
from django.utils import timezone
from helper.save_load import load_agents_from_newest, save_agents
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from walmart_model import WalmartModel

from .models import Cust1, Cust2, Products, SimulationRun, Transactions
from .serialization import (Cust1Serializer, Cust2Serializer,
                            ProductSerializer, SimulationInputSerializer,
                            TransactionSerializer)


# --- Setting up the simulation API to run and populate the graph
@dataclass
class RunState:
    inputs: Dict[str, Any]
    status: str = "running"  # "running" | "finished" | "error" | "stopped"
    steps: List[Dict[str, Any]] = field(default_factory=list)  # step metrics
    step: int = 0
    total_steps: int = 0
    started_at: str = field(default_factory=lambda: timezone.now().isoformat())
    error_msg: str | None = None


RUNS: Dict[str, RunState] = {}
RUN_LOCK = Lock()


def run_in_background(run_id: str, inputs: Dict[str, str | int]):
    """
    Build + run the Mesa model and push step metrics into RUNS[run_id].steps.

    Execution order:
      1) Initialize WalmartModel(**args, data_dir=DATA_DIR)
      2) model.check_load_match_index()
      3) model.initialize_extra_agents(...)
      4) For each day: model.step() -> map_metrics -> append RUNS[run_id].steps
      5) Save the files
      6) Load the files to PostgreSQL
    """
    try:
        days = int(inputs.get("max_steps", 0))
        if days <= 0:
            raise ValueError("max_steps must be > 0")

        model = WalmartModel(**inputs)
        loaded_file, loaded_id_dict, metadata = load_agents_from_newest(
            model, model.class_registry, mode="prod"
        )
        if loaded_file and loaded_id_dict and metadata:
            print(
                f"Agents loaded {len(loaded_id_dict)} with max id: {max(loaded_id_dict)}"
            )
            print(f"Metadata: {metadata}")
        else:
            print("No saved files")

        model.initialize_extra_agents()

        with RUN_LOCK:
            st = RUNS.get(run_id)
            if not st:
                return
            st.total_steps = days

        for s in range(1, days + 1):
            metrics = model.step()

            with RUN_LOCK:
                st = RUNS.get(run_id)
                if not st or st.status == "stopped":
                    break
                if metrics is not None:
                    st.steps.append(metrics)
                st.step = s

        with RUN_LOCK:
            st = RUNS.get(run_id)
            if st and st.status != "stopped":
                st.status = "finished"

        # Saving the files
        result_df = model.save_results_as_df()
        final_paths, model_id = model.write_results_csv(result_df)
        print(f"Model {model_id} is finished and saved!")
        saved_file, metadata = save_agents(model)
        for f in final_paths:
            assert f.exists(), print(f"Cannot find file {f}")

        assert saved_file.exists() & metadata.exists(), print(
            "Can't find recently saved file"
        )

    except Exception as e:
        err = f"{e}\n{traceback.format_exc()}"
        with RUN_LOCK:
            st = RUNS.get(run_id)
            if st:
                st.status = "error"
                st.error_msg = err


class StartSimulationView(APIView):
    """
    POST /api/simulate/
    Body: {
        "start_date": "20250818", (YYYYMMDD)
        "max_steps": 7,
        "n_customers1": 100,
        "n_customers2": 100,
        "n_products_per_category": 5
    }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SimulationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload: Dict[str, Any] = dict(serializer.validated_data)

        run_id = str(uuid.uuid4())
        with RUN_LOCK:
            RUNS[run_id] = RunState(
                inputs=payload, status="running", steps=[], step=0, total_steps=0
            )

        # Running the simulation with threads
        t = threading.Thread(
            target=run_in_background, args=(run_id, payload), daemon=True
        )
        t.start()
        return JsonResponse({"run_id": run_id}, status=status.HTTP_201_CREATED)


class RunProgressView(APIView):
    """
    GET    /api/simulate/<run_id>?since=<int>  -> { data: [...], finished: bool, error?: str }
    DELETE /api/simulate/<run_id>              -> reset/stop this run, clears memory
    """

    permission_classes = [AllowAny]

    def get(self, request, run_id: str):
        since = int(request.GET.get("since", 0))
        with RUN_LOCK:
            st = RUNS.get(run_id)
            if not st:
                raise Http404("Run not found")
            data = [d for d in st.steps if d["step"] > since]
            finished = st.status in ("finished", "error")
            resp = {"data": data, "finished": finished}
            if st.status == "error":
                resp["error"] = st.error_msg
            return JsonResponse(resp)

    def delete(self, request, run_id: str):
        with RUN_LOCK:
            st = RUNS.get(run_id)
            if st:
                st.status = "stopped"
                # wipe this run so UI is clean after reset
                RUNS.pop(run_id, None)
        return JsonResponse({"ok": True})


# --- Getting the table views for Dashboard ---
class TransactionListView(generics.ListAPIView):
    """
    GET /api/transactions/?since=<ISO>&limit=<int>
    Returns the most-recent transactions, filtered by date and capped by limit.
    """

    serializer_class = TransactionSerializer

    def get_queryset(self):
        qs = Transactions.objects.all().order_by("-date_purchased")
        since = self.request.query_params.get("since")
        limit = int(self.request.query_params.get("limit", 50))
        if since:
            qs = qs.filter(date_purchased__gte=since)
        else:
            qs = qs.filter(date_purchased__gte=timezone.now() - timedelta(days=365))
        return qs[:limit]


class BaseSpendingListView(generics.ListAPIView):
    """
    Base view for listing entities with total spending/sales data
    """

    def get_limit(self):
        """Get the limit from query parameters, default to 20"""
        return int(self.request.query_params.get("limit", 20))

    def get_queryset(self):
        """Override this method in subclasses"""
        raise NotImplementedError("Subclasses must implement get_queryset()")


class Cust1ListView(BaseSpendingListView):
    serializer_class = Cust1Serializer

    def get_queryset(self):
        limit = self.get_limit()

        raw_query = """
        SELECT c1.unique_id, 
               COALESCE(SUM(t.unit_price * t.quantity), 0) as total_sum
        FROM cust1 c1
        LEFT JOIN customers_lookup cl ON c1.unique_id = cl.external_id 
                                     AND cl.cust_type = 'cust1'
        LEFT JOIN transactions t ON cl.customer_id = t.unique_id
        GROUP BY c1.unique_id
        ORDER BY total_sum DESC
        LIMIT %s
        """

        return Cust1.objects.raw(raw_query, [limit])


class Cust2ListView(BaseSpendingListView):
    serializer_class = Cust2Serializer

    def get_queryset(self):
        limit = self.get_limit()

        raw_query = """
        SELECT c2.unique_id, 
               COALESCE(SUM(t.unit_price * t.quantity), 0) as total_sum
        FROM cust2 c2
        LEFT JOIN customers_lookup cl ON c2.unique_id = cl.external_id 
                                     AND cl.cust_type = 'cust2'
        LEFT JOIN transactions t ON cl.customer_id = t.unique_id
        GROUP BY c2.unique_id
        ORDER BY total_sum DESC
        LIMIT %s
        """

        return Cust2.objects.raw(raw_query, [limit])


class ProductListView(BaseSpendingListView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        limit = self.get_limit()

        raw_query = """
        SELECT p.product_id, 
               COALESCE(SUM(t.unit_price * t.quantity), 0) as total_sum
        FROM products p
        LEFT JOIN transactions t ON p.product_id = t.product_id
        GROUP BY p.product_id
        ORDER BY total_sum DESC
        LIMIT %s
        """

        return Products.objects.raw(raw_query, [limit])
