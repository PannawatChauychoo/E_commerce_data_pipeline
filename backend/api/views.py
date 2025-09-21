# pyright: reportMissingImports=false
import threading
import traceback
import uuid
import os
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List

from django.db.models import Case, DecimalField, F, Sum, When, Count, Avg
from django.http import Http404, JsonResponse, HttpResponse, FileResponse
import zipfile
import io
from django.utils import timezone
from django.db import connection
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


# --- Simple file-based helper functions (no database dependency)
def check_agm_output_exists():
    """
    Simple check: does agm_output folder have any run directories?
    This determines if continuation is possible.
    """
    try:
        data_source_path = Path(__file__).resolve().parent.parent.parent / 'data_pipeline' / 'data_source' / 'agm_output'
        
        if not data_source_path.exists():
            return False
            
        # Check if there are any run directories
        run_dirs = [d for d in data_source_path.iterdir() if d.is_dir() and d.name.startswith('run_time=')]
        return len(run_dirs) > 0
    except Exception:
        return False


def get_latest_csv_metrics():
    """
    Read the latest metrics CSV file from agm_output folder.
    Uses the same structure as WalmartModel.get_current_step_metrics_for_graphs()
    Returns formatted data for frontend charts.
    """
    try:
        data_source_path = Path(__file__).resolve().parent.parent.parent / 'data_pipeline' / 'data_source' / 'agm_output'

        if not data_source_path.exists():
            return None

        # Find the most recent run directory
        run_dirs = [d for d in data_source_path.iterdir() if d.is_dir() and d.name.startswith('run_time=')]
        if not run_dirs:
            return None

        latest_run_dir = max(run_dirs, key=lambda x: x.stat().st_mtime)

        # Find the metrics CSV file
        metrics_files = list(latest_run_dir.glob('id=*_metrics.csv'))
        if not metrics_files:
            return None

        metrics_file = metrics_files[0]

        # Read CSV file using pandas for better data handling
        import pandas as pd
        df = pd.read_csv(metrics_file)

        metrics = []
        latest_simulated_date = None

        for idx, row in df.iterrows():
            # Use the same structure as get_current_step_metrics_for_graphs()
            step_metrics = {
                'step': idx + 1,
                'current_date': str(row.get('Current Date', '')),
                'cust1_avg_purchase': float(row.get('Avg_Purchases_Cust1', 0)),
                'cust2_avg_purchase': float(row.get('Avg_Purchases_Cust2', 0)),
                'total_daily_purchases': int(row.get('Total_Daily_Purchase', 0)),
                'total_cust1': int(row.get('Total_cust1', 0)),
                'total_cust2': int(row.get('Total_cust2', 0)),
                'total_products': int(row.get('Total_products', 0)),
                'stockout_rate': float(row.get('Stockout', 0))
            }
            metrics.append(step_metrics)

            # Track the latest simulated date from the Current Date column
            if step_metrics['current_date']:
                latest_simulated_date = step_metrics['current_date']

        return {
            'metrics': metrics,
            'run_dir': latest_run_dir.name,
            'metrics_file': metrics_file.name,
            'total_steps': len(metrics),
            'latest_simulated_date': latest_simulated_date
        }
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None


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
    Uses your existing WalmartModel logic - it already handles continuation automatically.
    """
    try:
        days = int(inputs.get("max_steps", 0))
        if days <= 0:
            raise ValueError("max_steps must be > 0")

        # Initialize WalmartModel with your existing parameters
        model = WalmartModel(
            start_date=inputs.get('start_date'),
            max_steps=days,
            n_customers1=inputs.get('n_customers1', 100),
            n_customers2=inputs.get('n_customers2', 100),
            n_products_per_category=inputs.get('n_products_per_category', 5),
            mode='prod'
        )
        
        # Use your existing agent loading logic
        loaded_file, loaded_id_dict, metadata = load_agents_from_newest(
            model, model.class_registry, mode="prod"
        )
        if loaded_file and loaded_id_dict and metadata:
            print(f"Agents loaded {len(loaded_id_dict)} with max id: {max(loaded_id_dict)}")
        else:
            print("No saved files - starting fresh simulation")

        model.initialize_extra_agents()

        with RUN_LOCK:
            st = RUNS.get(run_id)
            if not st:
                return
            st.total_steps = days

        # Run simulation steps
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

        # Save results using your existing logic
        result_df = model.save_results_as_df()
        final_paths, model_id = model.write_results_csv(result_df)
        print(f"Model {model_id} is finished and saved!")
        
        saved_file, metadata = save_agents(model, keep_last=5, mode="prod")
        for f in final_paths:
            assert f.exists(), print(f"Cannot find file {f}")

        assert saved_file.exists() & metadata.exists(), print(
            "Can't find recently saved file"
        )

    except Exception as e:
        err = f"{e}\n{traceback.format_exc()}"
        print(f"Simulation error: {err}")
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
        
        # Simple continuation check - your WalmartModel handles the rest
        continue_existing = payload.get('continue_existing', False)
        if continue_existing:
            print("Continue mode requested - WalmartModel will handle continuation logic")
        
        with RUN_LOCK:
            RUNS[run_id] = RunState(
                inputs=payload, 
                status="running", 
                steps=[], 
                step=0, 
                total_steps=0
            )

        # Running the simulation with threads - your existing logic
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
                # Handle container restart gracefully - assume simulation finished
                return JsonResponse({
                    "data": [],
                    "finished": True,
                    "error": "Simulation interrupted by server restart. Please start a new simulation."
                })
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


class HealthCheckView(APIView):
    """
    GET /api/health/ -> Simple health check (no file dependencies)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return JsonResponse({'status': 'healthy', 'service': 'walmart-simulation-api'})


class ContinuityCheckView(APIView):
    """
    GET /api/simulate/can-continue/ -> Simple check if agm_output has files
    """
    permission_classes = [AllowAny]

    def get(self, request):
        can_continue = check_agm_output_exists()
        return JsonResponse({'can_continue': can_continue})


class SimulationPreviewView(APIView):
    """
    GET /api/simulate/preview/ -> Load CSV metrics from agm_output folder
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            csv_info = get_latest_csv_metrics()
            
            if not csv_info:
                return JsonResponse({
                    'preview_data': [],
                    'has_data': False,
                    'message': 'No CSV files found in agm_output folder'
                })
            
            return JsonResponse({
                'preview_data': csv_info['metrics'],
                'has_data': True,
                'run_info': {
                    'run_dir': csv_info['run_dir'],
                    'metrics_file': csv_info['metrics_file']
                },
                'total_historical_steps': csv_info['total_steps'],
                'latest_simulated_date': csv_info.get('latest_simulated_date'),
                'message': f'Loaded {csv_info["total_steps"]} steps from {csv_info["run_dir"]}'
            })
            
        except Exception as e:
            return JsonResponse({
                'error': f'Failed to load CSV: {str(e)}',
                'preview_data': [],
                'has_data': False
            }, status=500)


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


# --- File Management Views ---
def get_agm_output_files():
    """
    Scan agm_output folder and return structured file information
    """
    try:
        data_source_path = Path(__file__).resolve().parent.parent.parent / 'data_pipeline' / 'data_source' / 'agm_output'

        if not data_source_path.exists():
            return []

        runs = []
        run_dirs = [d for d in data_source_path.iterdir() if d.is_dir() and d.name.startswith('run_time=')]

        for run_dir in sorted(run_dirs, key=lambda x: x.stat().st_mtime, reverse=True):
            # Extract date from folder name: run_time=2024-09-17
            date_str = run_dir.name.replace('run_time=', '')

            files = []
            csv_files = list(run_dir.glob('id=*_*.csv'))

            for csv_file in csv_files:
                # Extract file type from filename: id=123456_transactions.csv -> transactions
                filename_parts = csv_file.name.split('_')
                if len(filename_parts) >= 2:
                    file_type = filename_parts[1].replace('.csv', '')
                    file_size = csv_file.stat().st_size

                    # Format file size
                    if file_size < 1024:
                        size_str = f"{file_size} B"
                    elif file_size < 1024 * 1024:
                        size_str = f"{file_size / 1024:.1f} KB"
                    else:
                        size_str = f"{file_size / (1024 * 1024):.1f} MB"

                    files.append({
                        'name': file_type,
                        'size': size_str,
                        'path': str(csv_file.relative_to(data_source_path)),
                        'full_filename': csv_file.name,
                        'modified': csv_file.stat().st_mtime
                    })

            if files:  # Only include runs that have CSV files
                # Extract run ID from first file
                run_id = None
                if files:
                    first_file = files[0]['full_filename']
                    if first_file.startswith('id='):
                        run_id = first_file.split('_')[0].replace('id=', '')

                runs.append({
                    'id': run_id or 'unknown',
                    'date': date_str,
                    'time': run_dir.stat().st_ctime,  # Use creation time as approximate time
                    'files': sorted(files, key=lambda x: x['name'])
                })

        return runs

    except Exception as e:
        print(f"Error scanning agm_output files: {e}")
        return []


class FileListView(APIView):
    """
    GET /api/files/list/ -> List all simulation runs and their CSV files
    """
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            files = get_agm_output_files()
            return JsonResponse({
                'runs': files,
                'total_runs': len(files)
            })
        except Exception as e:
            return JsonResponse({
                'error': f'Failed to list files: {str(e)}',
                'runs': [],
                'total_runs': 0
            }, status=500)


class FileDownloadView(APIView):
    """
    GET /api/files/download/<str:file_path>/ -> Download a specific CSV file
    """
    permission_classes = [AllowAny]

    def get(self, request, file_path: str):
        try:
            data_source_path = Path(__file__).resolve().parent.parent.parent / 'data_pipeline' / 'data_source' / 'agm_output'

            # Construct full file path
            full_file_path = data_source_path / file_path

            # Security check: ensure file is within agm_output directory
            if not str(full_file_path.resolve()).startswith(str(data_source_path.resolve())):
                return JsonResponse({'error': 'Invalid file path'}, status=400)

            if not full_file_path.exists():
                return JsonResponse({'error': 'File not found'}, status=404)

            if not full_file_path.is_file():
                return JsonResponse({'error': 'Path is not a file'}, status=400)

            # Create file response
            response = FileResponse(
                open(full_file_path, 'rb'),
                as_attachment=True,
                filename=full_file_path.name
            )
            response['Content-Type'] = 'text/csv'

            return response

        except Exception as e:
            return JsonResponse({
                'error': f'Failed to download file: {str(e)}'
            }, status=500)


class BulkDownloadView(APIView):
    """
    GET /api/files/bulk-download/<str:run_id>/ -> Download all CSV files in a run as zip
    """
    permission_classes = [AllowAny]

    def get(self, request, run_id: str):
        try:
            data_source_path = Path(__file__).resolve().parent.parent.parent / 'data_pipeline' / 'data_source' / 'agm_output'

            # Find the run folder that contains files with this run_id
            run_folder = None
            for folder in data_source_path.iterdir():
                if folder.is_dir() and folder.name.startswith('run_time='):
                    # Check if any CSV files in this folder have the run_id
                    csv_files = list(folder.glob(f'id={run_id}_*.csv'))
                    if csv_files:
                        run_folder = folder
                        break

            if not run_folder:
                return JsonResponse({'error': 'Run not found'}, status=404)

            # Find all CSV files for this run_id
            csv_files = list(run_folder.glob(f'id={run_id}_*.csv'))
            if not csv_files:
                return JsonResponse({'error': 'No CSV files found for this run'}, status=404)

            # Create zip file in memory
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add each CSV file to zip
                for csv_file in csv_files:
                    # Use a cleaner filename in the zip (remove the id= prefix)
                    clean_name = csv_file.name.replace(f'id={run_id}_', '')
                    zip_file.write(csv_file, clean_name)

            zip_buffer.seek(0)

            # Create response with zip file
            response = HttpResponse(
                zip_buffer.getvalue(),
                content_type='application/zip'
            )
            response['Content-Disposition'] = f'attachment; filename="simulation_{run_id}.zip"'

            return response

        except Exception as e:
            return JsonResponse({
                'error': f'Failed to create zip file: {str(e)}'
            }, status=500)
