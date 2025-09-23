// SimulationVisualization.tsx
"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import {
  ResponsiveContainer,
  LineChart as RLineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  BarChart as RBarChart,
  Bar,
  Cell,
} from "recharts";

const API_ORIGIN = process.env.NEXT_PUBLIC_API_ORIGIN ?? "http://localhost:8000";


/* ---------- Updated Color system using CSS custom properties ---------- */
const getChartColors = (isDark: boolean) => {
  if (typeof window === 'undefined') return {
    grid: '#e5e7eb',
    axis: '#1f2937',
    primary: '#3b82f6',      // Light mode: blue, Dark mode: orange
    secondary: '#ea580c',    // Light mode: orange, Dark mode: blue
    accent: '#fb923c',       // Accent color for variety
  };

  const style = getComputedStyle(document.documentElement);

  return {
    grid: `hsl(${style.getPropertyValue('--border')})`,
    axis: isDark ? '#e5e7eb' : '#374151', // High contrast: light gray in dark mode, dark gray in light mode
    primary: isDark ? '#fb923c' : '#3b82f6',      // Dark mode: orange, Light mode: blue
    secondary: isDark ? '#60a5fa' : '#ea580c',    // Dark mode: blue, Light mode: orange
    accent: isDark ? '#fdba74' : '#fb923c',       // Lighter shade for accents
  };
};

/* ---------- Types ---------- */
type SimInputs = {
  start_date: string;
  max_steps: number;
  n_customers1: number;
  n_customers2: number;
  n_products_per_category: number;
};

/** Raw step payload as returned by your model.step() on the server */
type StepMetricsRaw = {
  step: number;
  current_date: string;
  cust1_avg_purchase: number;
  cust2_avg_purchase: number;
  total_daily_purchases: number;
  total_cust1: number;
  total_cust2: number;
  total_products: number;
  stockout_rate: number;
};


// Choosing colors for barchart using theme-aware color scheme
const getBarColor = (name: string, isDark: boolean) => {
  const colors = getChartColors(isDark);
  switch (name) {
    case "Customers1":
      return colors.primary;   // Theme primary: blue (light) / orange (dark)
    case "Customers2":
      return colors.secondary; // Theme secondary: orange (light) / blue (dark)
    case "Products":
      return colors.accent;    // Accent color for variety
    default:
      return colors.primary;
  }
};


/* ---------- Helpers ---------- */
function fmtElapsed(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function addDays(isoYYYYMMDD: string, delta: number): string {
  const d = new Date(isoYYYYMMDD + "T00:00:00");
  if (Number.isNaN(d.getTime())) return isoYYYYMMDD;
  d.setDate(d.getDate() + delta);
  return d.toISOString().slice(0, 10);
}

// Convert YYYY-MM-DD to YYYYMMDD
function formatDateForAPI(dateStr: string): string {
  return dateStr.replace(/-/g, '');
}

// Convert YYYYMMDD or float to MM/DD/YY format
function formatDateForInput(dateStr: string | number): string {
  const str = String(dateStr);

  // Handle float format like 20250101.0
  if (str.includes('.')) {
    const cleanStr = str.split('.')[0];
    if (cleanStr.length === 8) {
      const year = cleanStr.slice(2, 4); // Get last 2 digits of year
      const month = cleanStr.slice(4, 6);
      const day = cleanStr.slice(6, 8);
      return `${month}/${day}/${year}`;
    }
  }

  // Handle YYYYMMDD format
  if (str.length === 8) {
    const year = str.slice(2, 4); // Get last 2 digits of year
    const month = str.slice(4, 6);
    const day = str.slice(6, 8);
    return `${month}/${day}/${year}`;
  }

  // Handle YYYY-MM-DD format
  if (str.includes('-') && str.length === 10) {
    const parts = str.split('-');
    const year = parts[0].slice(2); // Get last 2 digits
    const month = parts[1];
    const day = parts[2];
    return `${month}/${day}/${year}`;
  }

  return str;
}

// Custom Tooltip Component for Line Charts
const CustomLineTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) return null;

  return (
    <div className="bg-gray-100 border border-gray-300 rounded-md px-2 py-1 text-xs shadow-sm">
      <p className="font-medium text-gray-800 mb-1">{label}</p>
      {payload.map((entry: any, index: number) => (
        <div key={index} className="flex items-center gap-1">
          <div
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-gray-700">
            {entry.name}: {Math.round(entry.value)}
          </span>
        </div>
      ))}
    </div>
  );
};

// Calculate evenly spaced Y-axis with explicit ticks
function calculateEvenYAxis(data: any[], dataKey: string, tickCount: number = 5): { domain: [number, number], ticks: number[] } {
  if (!data.length) return { domain: [0, 1], ticks: [] };

  const values = data.map(d => Number(d[dataKey]) || 0);
  const maxValue = Math.max(...values);

  if (maxValue === 0) return { domain: [0, 1], ticks: [] };

  // Calculate nice step size
  const roughStep = maxValue / (tickCount - 1);
  const magnitude = Math.pow(10, Math.floor(Math.log10(roughStep)));
  const normalizedStep = roughStep / magnitude;

  let niceStep;
  if (normalizedStep <= 1) niceStep = 1;
  else if (normalizedStep <= 2) niceStep = 2;
  else if (normalizedStep <= 5) niceStep = 5;
  else niceStep = 10;

  const step = niceStep * magnitude;
  const finalTick = Math.ceil(maxValue / step) * step;
  const paddedMax = Math.max(finalTick, maxValue * 1.1);

  // Generate explicit tick array, always starting with 0
  const ticks = [0];
  for (let i = step; i <= finalTick; i += step) {
    ticks.push(i);
  }

  // Remove final tick if it's too close to the previous one
  if (ticks.length > 1 && (ticks[ticks.length - 1] - ticks[ticks.length - 2]) < step * 0.5) {
    ticks.pop();
  }

  return { domain: [0, paddedMax], ticks };
}

/* ---------- Component ---------- */
interface SimulationWorkspaceProps {
  onSimulationComplete?: () => void;
}

export default function SimulationWorkspace({ onSimulationComplete }: SimulationWorkspaceProps) {
  /* Inputs (left panel) */
  const [inputs, setInputs] = useState<SimInputs>({
    max_steps: 7,
    n_customers1: 100,
    n_customers2: 100,
    start_date: '2025-01-01',
    n_products_per_category: 5,
  });

  /* Run state */
  const [running, setRunning] = useState(false);
  const [runId, setRunId] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState<number>(0); // seconds
  const [series, setSeries] = useState<StepMetricsRaw[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  /* Preview and Continue functionality */
  const [previewData, setPreviewData] = useState<StepMetricsRaw[]>([]);
  const [canContinue, setCanContinue] = useState(false);
  const [loadingPreview, setLoadingPreview] = useState(false);

  /* Theme detection for reactive colors */
  const [isDark, setIsDark] = useState(false);

  /* Timers */
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const labelRef = useRef<ReturnType<typeof setInterval> | null>(null);

  /* Chart container ref for auto-scroll */
  const chartContainerRef = useRef<HTMLDivElement>(null);
  /* Sidebar ref to measure height */
  const sidebarRef = useRef<HTMLDivElement>(null);
  /* State to track sidebar height */
  const [sidebarHeight, setSidebarHeight] = useState<number>(0);


  /* Measure sidebar height on mount and window resize */
  useEffect(() => {
    const measureHeight = () => {
      if (sidebarRef.current) {
        setSidebarHeight(sidebarRef.current.offsetHeight);
      }
    };

    measureHeight();
    window.addEventListener('resize', measureHeight);
    return () => window.removeEventListener('resize', measureHeight);
  }, []);

  /* Update height when sidebar content changes */
  useEffect(() => {
    if (sidebarRef.current) {
      setSidebarHeight(sidebarRef.current.offsetHeight);
    }
  }, [inputs, running, series.length]);

  /* Check if we can continue from previous simulation */
  const checkCanContinue = useCallback(async () => {
    try {
      // First check if API is healthy
      const healthResponse = await fetch(`${API_ORIGIN}/api/health/`, {
        credentials: 'include',
      });
      if (!healthResponse.ok) {
        setCanContinue(false);
        return;
      }

      // Then check if previous simulation data exists
      const continueResponse = await fetch(`${API_ORIGIN}/api/simulate/can-continue/`, {
        credentials: 'include',
      });
      const continueData = await continueResponse.json();
      setCanContinue(continueData.can_continue || false);
    } catch (error) {
      console.error('Error checking continuation:', error);
      setCanContinue(false);
    }
  }, []);

  /* Load preview data from previous simulation */
  const loadPreview = useCallback(async () => {
    setLoadingPreview(true);
    try {
      const response = await fetch(`${API_ORIGIN}/api/simulate/preview/`, {
        credentials: 'include',
      });
      const data = await response.json();

      if (data.has_data && data.preview_data) {
        setPreviewData(data.preview_data);
      } else {
        setPreviewData([]);
      }
    } catch (error) {
      console.error('Error loading preview:', error);
      setPreviewData([]);
    } finally {
      setLoadingPreview(false);
    }
  }, []);

  /* Check continuation possibility on mount */
  useEffect(() => {
    checkCanContinue();
  }, [checkCanContinue]);

  /* Theme detection - listen for theme changes */
  useEffect(() => {
    const updateTheme = () => {
      if (typeof window !== 'undefined') {
        setIsDark(document.documentElement.classList.contains('dark'));
      }
    };

    // Initial theme detection
    updateTheme();

    // Listen for theme changes using MutationObserver
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
          updateTheme();
        }
      });
    });

    if (typeof window !== 'undefined') {
      observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['class']
      });
    }

    return () => observer.disconnect();
  }, []);


  /* Derived series for charts - combine preview data with live simulation */
  const avgPurchasesSeries = useMemo(
    () => {
      const combined = [...previewData, ...series];
      return combined.map((d) => ({
        label: d.current_date ? formatDateForInput(d.current_date) : addDays(inputs.start_date, Math.max(0, (d.step ?? 1) - 1)),
        cust1: Number(d.cust1_avg_purchase ?? 0),
        cust2: Number(d.cust2_avg_purchase ?? 0),
      }));
    },
    [series, previewData, inputs.start_date]
  );

  const totalPurchasesSeries = useMemo(
    () => {
      const combined = [...previewData, ...series];
      return combined.map((d) => ({
        label: d.current_date ? formatDateForInput(d.current_date) : addDays(inputs.start_date, Math.max(0, (d.step ?? 1) - 1)),
        value: Number(d.total_daily_purchases ?? 0),
      }));
    },
    [series, previewData, inputs.start_date]
  );

  const stockoutSeries = useMemo(
    () => {
      const combined = [...previewData, ...series];
      console.log('Processing stockout data:', combined.map(d => ({
        step: d.step,
        stockout_rate: d.stockout_rate,
        total_products: d.total_products
      })));

      const rawSeries = combined.map((d) => {
        // Use actual total_products from backend data
        // Fallback to a reasonable estimate only if total_products is missing entirely
        const totalProducts = Number(d.total_products) || (inputs.n_products_per_category * 34);

        return {
          label: d.current_date ? formatDateForInput(d.current_date) : addDays(inputs.start_date, Math.max(0, (d.step ?? 1) - 1)),
          value: Number(d.stockout_rate ?? 0),
          totalProducts: totalProducts,
        };
      });

      // Check if we should show counts vs percentages
      const maxStockoutRate = Math.max(...rawSeries.map(d => d.value));
      const shouldShowCounts = maxStockoutRate < 10;

      console.log('Stockout calculation:', {
        maxStockoutRate,
        shouldShowCounts,
        sampleData: rawSeries.slice(0, 3).map(d => ({
          label: d.label,
          originalRate: d.value,
          totalProducts: d.totalProducts,
          calculatedValue: shouldShowCounts ? Math.round((d.value / 100) * d.totalProducts) : d.value
        }))
      });

      return rawSeries.map((d) => ({
        label: d.label,
        value: shouldShowCounts
          ? Math.round((d.value / 100) * d.totalProducts) // Convert percentage to actual count
          : d.value, // Keep as percentage
      }));
    },
    [series, previewData, inputs.start_date, inputs.n_products_per_category]
  );

  const totalsBar = useMemo(() => {
    const last = series.at(-1);

    // Use actual backend data when available
    const totalCustomers1 = Number(last?.total_cust1 ?? 0);
    const totalCustomers2 = Number(last?.total_cust2 ?? 0);
    const totalProducts = Number(last?.total_products ?? 0);

    console.log('Bar graph data:', {
      lastSeriesItem: last,
      totalCustomers1,
      totalCustomers2,
      totalProducts,
      fallbacks: {
        customers1: inputs.n_customers1,
        customers2: inputs.n_customers2,
        products: inputs.n_products_per_category * 34
      }
    });

    return [
      { name: "Customers1", value: totalCustomers1 || inputs.n_customers1 },
      { name: "Customers2", value: totalCustomers2 || inputs.n_customers2 },
      { name: "Products", value: totalProducts || inputs.n_products_per_category * 34 },
    ];
  }, [series, inputs]);

  /* Input handler for text/date inputs */
  const onChange =
    (key: keyof SimInputs) =>
      (e: React.ChangeEvent<HTMLInputElement>) => {
        const v = e.target.value;
        setInputs((s) => ({
          ...s,
          [key]:
            key === "start_date"
              ? v
              : Number.parseInt(v, 10),
        }));

        // Reset series when max_steps changes to show correct progress
        if (key === "max_steps") {
          setSeries([]);
          setPreviewData([]);
        }
      };

  /* Slider handler for numeric inputs */
  const onSliderChange =
    (key: keyof SimInputs) =>
      (value: number[]) => {
        setInputs((s) => ({
          ...s,
          [key]: value[0],
        }));
      };

  /* Reset logic (replaces Stop) */
  const reset = useCallback(async () => {
    if (pollRef.current) clearInterval(pollRef.current);
    if (labelRef.current) clearInterval(labelRef.current);
    pollRef.current = null;
    labelRef.current = null;

    if (runId) {
      // Ask backend to stop & clear; ignore errors
      try {
        await fetch(`/api/simulate/${runId}`, { method: "DELETE" });
      } catch {
        /* noop */
      }
    }

    // Call the comprehensive reset endpoint to clear all temporary data
    try {
      const response = await fetch(`${API_ORIGIN}/api/reset/`, {
        method: 'POST',
        credentials: 'include',
      });
      if (response.ok) {
        console.log('Successfully reset all temporary data');
      } else {
        console.warn('Failed to reset temporary data:', response.status);
      }
    } catch (error) {
      console.error('Error calling reset endpoint:', error);
    }

    // Reset frontend state
    setRunId(null);
    setElapsed(0);
    setRunning(false);
    setSeries([]);
    setErrorMsg(null);
    setPreviewData([]);

    // Update continuation state to reflect that there's no previous data
    setCanContinue(false);
  }, [runId]);

  /* Cleanup on unmount */
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
      if (labelRef.current) clearInterval(labelRef.current);
    };
  }, []);

  const getCSRFCookie = () => {
    const m = document.cookie.match(/(?:^|;)\s*csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : null;
  };

  type ProgressResponse = {
    data: Array<{ step: number;[k: string]: any }>;
    finished: boolean;
    error?: string | null;
  };

  const clearTimers = () => {
    if (labelRef.current !== null) { clearInterval(labelRef.current); labelRef.current = null; }
    if (pollRef.current !== null) { clearInterval(pollRef.current); pollRef.current = null; }
  };

  /* Start a run: submit -> timer; poll until finished */
  const start = async () => {
    // ---- early cleanup to prevent stacked timers if user clicks twice
    clearTimers();

    console.log("Starting simulation with inputs:", inputs);
    setSeries([]);
    setErrorMsg(null);
    setRunning(true);
    setElapsed(0);

    // Auto-scroll to chart container
    setTimeout(() => {
      chartContainerRef.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    }, 100);

    // Button timer
    const t0 = Date.now();
    labelRef.current = setInterval(() => {
      setElapsed(Math.floor((Date.now() - t0) / 1000));
    }, 250);

    const payload = {
      ...inputs,
      // ensure API gets YYYYMMDD
      start_date: formatDateForAPI(inputs.start_date),
      continue_existing: canContinue, // Auto-continue if previous data exists
    };

    // derive max steps from either max_steps or days
    const maxSteps = Number(payload.max_steps ?? 0);

    // ---- Kick off backend run
    try {
      const csrf = getCSRFCookie();
      const res = await fetch(`${API_ORIGIN}/api/simulate/`, {
        method: "POST",
        credentials: "include",           // allow cookies/session
        headers: {
          "Content-Type": "application/json",
          ...(csrf ? { "X-CSRFToken": csrf } : {}),
        },
        body: JSON.stringify(payload),
      });

      console.log("Response status:", res.status);

      if (!res.ok) throw new Error((await res.text()) || `Server error: ${res.status}`);

      const { run_id } = await res.json();
      console.log("Run started:", run_id);
      setRunId(run_id);

      // ---- Polling
      let since = 0;
      pollRef.current = setInterval(async () => {
        try {
          const r = await fetch(`${API_ORIGIN}/api/simulate/${run_id}?since=${since}`, {
            credentials: "include",
            headers: { "Accept": "application/json" },
          });

          if (!r.ok) {
            const msg = await r.text();
            throw new Error(msg || `Polling failed: ${r.status}`);
          }

          const { data, finished, error }: ProgressResponse = await r.json();

          if (Array.isArray(data) && data.length) {
            setSeries(prev => {
              // dedupe in case server re-sends the last item
              const next = [...prev];
              for (const d of data) {
                //@ts-expect-error
                if (!next.length || d.step > next[next.length - 1].step) next.push(d);
              }
              since = next[next.length - 1]?.step ?? since; // advance cursor
              return next;
            });
          }

          const gotAll = maxSteps > 0 && since >= maxSteps;
          if (finished || gotAll || error) {
            clearTimers();
            setRunning(false);
            if (error) {
              setErrorMsg(error);
            } else {
              // Simulation completed successfully - trigger notification and re-check continuation
              onSimulationComplete?.();
              checkCanContinue(); // Re-check if we can continue after completion
            }
          }
        } catch (err: any) {
          console.error("Polling error:", err);
          clearTimers();
          setRunning(false);
          setErrorMsg(err?.message ?? "Polling error");
        }
      }, 600);
    } catch (e: any) {
      clearTimers();
      setRunning(false);
      setErrorMsg(e?.message ?? "Failed to start");
    }
  };

  /* ---------- UI ---------- */
  const inputClass = "bg-input border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus-visible:ring-0";

  const chartColors = useMemo(() => getChartColors(isDark), [isDark]);

  return (
    <div className="w-full">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-foreground mb-2">Simulation Workspace</h2>
        <p className="text-muted-foreground">Configure parameters and run real-time customer behavior simulation</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left panel: inputs + controls */}
        <Card className="lg:col-span-3 bg-card border-border" ref={sidebarRef}>
          <CardHeader>
            <CardTitle className="text-lg text-foreground">Simulation Parameters</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">

            {/* Status info */}
            <div className="bg-muted/30 border border-border rounded-lg p-3 text-xs space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-medium text-foreground">Status</span>
                <span className={`px-2 py-1 rounded text-xs ${running ? 'bg-green-500/20 text-green-400' :
                  series.length > 0 ? 'bg-blue-500/20 text-blue-400' :
                    'bg-muted-foreground/20 text-muted-foreground'
                  }`}>
                  {running ? 'Running' : series.length > 0 ? 'Complete' : 'Ready'}
                </span>
              </div>
              {runId && (
                <div className="text-muted-foreground">
                  <span>Run ID: </span><span className="font-mono">{runId.slice(-8)}</span>
                </div>
              )}
              <div className="text-muted-foreground">
                Steps: {series.length} / {Number.isNaN(inputs.max_steps) ? 0 : inputs.max_steps}
              </div>
            </div>

            {/* Start of Inputs */}
            <div className="space-y-2">
              <Label htmlFor="start_date" className="text-sm font-medium text-foreground">Start Date</Label>
              <Input
                id="start_date"
                type="date"
                value={inputs.start_date}
                onChange={onChange("start_date")}
                className={inputClass}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="days" className="text-sm font-medium text-foreground">Simulation Days</Label>
              <Input
                id="days"
                type="number"
                min={1}
                value={inputs.max_steps}
                onChange={onChange("max_steps")}
                className={inputClass}
              />
            </div>

            {/* Type 1 Customers Slider */}
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <Label className="text-sm font-medium text-foreground">Type 1 Customers</Label>
                <span className="text-sm font-medium text-white">{inputs.n_customers1}</span>
              </div>
              <Slider
                value={[inputs.n_customers1]}
                onValueChange={onSliderChange("n_customers1")}
                min={0}
                max={1000}
                step={10}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>0</span>
                <span>1,000</span>
              </div>
            </div>

            {/* Type 2 Customers Slider */}
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <Label className="text-sm font-medium text-foreground">Type 2 Customers</Label>
                <span className="text-sm font-medium text-white">{inputs.n_customers2}</span>
              </div>
              <Slider
                value={[inputs.n_customers2]}
                onValueChange={onSliderChange("n_customers2")}
                min={0}
                max={1000}
                step={10}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>0</span>
                <span>1,000</span>
              </div>
            </div>

            {/* Products Per Category Slider */}
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <Label className="text-sm font-medium text-foreground">Products Per Category</Label>
                <span className="text-sm font-medium text-white">{inputs.n_products_per_category}</span>
              </div>
              <Slider
                value={[inputs.n_products_per_category]}
                onValueChange={onSliderChange("n_products_per_category")}
                min={1}
                max={20}
                step={1}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>1</span>
                <span>20</span>
              </div>
            </div>

            <div className="flex flex-col gap-3 pt-4 border-t border-border">

              {/* Load Preview Button */}
              <Button
                onClick={loadPreview}
                disabled={loadingPreview}
                variant="outline"
                className="w-full"
              >
                {loadingPreview ? (
                  <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-foreground border-t-transparent"></div>
                    Loading...
                  </div>
                ) : (
                  "Load Previous Data"
                )}
              </Button>

              <Button
                onClick={start}
                disabled={running}
                className="w-full bg-primary text-primary-foreground hover:bg-primary/90 font-medium"
                size="lg"
              >
                {running ? (
                  <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-background border-t-transparent"></div>
                    Running {fmtElapsed(elapsed)}
                  </div>
                ) : (
                  canContinue ? "Continue Simulation" : "Start Simulation"
                )}
              </Button>

              <Button
                onClick={reset}
                variant="outline"
                className="w-full"
              >
                Reset All
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Right panel: 3-row chart layout */}
        <div className="lg:col-span-9" ref={chartContainerRef}>
          <div
            className="grid grid-cols-5 grid-rows-3 gap-4"
            style={{ height: sidebarHeight > 0 ? `${sidebarHeight}px` : 'auto' }}
          >

            {/* Row 1: Average Purchase (3 cols, 1 row) */}
            {/* Average purchases per customer type - 3 cols, 1 row */}
            <Card className="col-span-3 row-span-1 bg-card border-border flex flex-col">
              <CardHeader className="flex-shrink-0">
                <CardTitle className="text-foreground">Average Number of Daily Purchases</CardTitle>
              </CardHeader>
              <CardContent className="flex-1 min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                  <RLineChart data={avgPurchasesSeries}>
                    <CartesianGrid stroke={chartColors.grid} strokeDasharray="3 3" />
                    <XAxis
                      dataKey="label"
                      axisLine={{ stroke: chartColors.axis, strokeWidth: 1 }}
                      tickLine={{ stroke: chartColors.axis, strokeWidth: 1 }}
                      tick={{ fill: chartColors.axis, fontSize: 11 }}
                      height={40}
                      tickFormatter={(value) => {
                        if (!value) return '';
                        if (value.includes('/')) return value; // Already in MM/DD/YY format
                        return formatDateForInput(value);
                      }}
                    />
                    <YAxis
                      axisLine={{ stroke: chartColors.axis, strokeWidth: 1 }}
                      tickLine={{ stroke: chartColors.axis, strokeWidth: 1 }}
                      tick={{ fill: chartColors.axis, fontSize: 11 }}
                      width={40}
                      {...(() => {
                        // Calculate domain based on max value from both cust1 and cust2
                        const allValues = avgPurchasesSeries.flatMap(d => [Number(d.cust1) || 0, Number(d.cust2) || 0]);
                        const maxValue = Math.max(...allValues);
                        const { domain, ticks } = calculateEvenYAxis([{value: maxValue}], 'value');
                        return {
                          domain,
                          ticks: ticks.length > 0 ? ticks : undefined
                        };
                      })()}
                    />
                    <Tooltip content={<CustomLineTooltip />} />
                    <Legend wrapperStyle={{ color: chartColors.axis, fontSize: '12px' }} />
                    <Line
                      type="monotone"
                      dataKey="cust1"
                      name="Type 1"
                      stroke={chartColors.primary}
                      strokeWidth={2.5}
                      dot={false}
                      activeDot={{ r: 4 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="cust2"
                      name="Type 2"
                      stroke={chartColors.secondary}
                      strokeWidth={2.5}
                      dot={false}
                      activeDot={{ r: 4 }}
                    />
                  </RLineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Entity counts - 2 cols, 2 rows */}
            <Card className="col-span-2 row-span-2 bg-card border-border flex flex-col">
              <CardHeader className="flex-shrink-0">
                <CardTitle className="text-foreground">Entity Counts</CardTitle>
              </CardHeader>
              <CardContent className="flex-1 min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                  <RBarChart data={totalsBar}>
                    <CartesianGrid stroke={chartColors.grid} strokeDasharray="3 3" />
                    <XAxis
                      dataKey="name"
                      axisLine={{ stroke: chartColors.axis }}
                      tickLine={{ stroke: chartColors.axis }}
                      tick={{ fill: chartColors.axis, fontSize: 11 }}
                      height={50}
                      angle={-45}
                      textAnchor="end"
                      interval={0}
                    />
                    <YAxis
                      axisLine={{ stroke: chartColors.axis }}
                      tickLine={{ stroke: chartColors.axis }}
                      tick={{ fill: chartColors.axis, fontSize: 11 }}
                      width={50}
                    />
                    <Bar
                      dataKey="value"
                      name="Count"
                      fillOpacity={0.8}
                      radius={[4, 4, 0, 0]}
                      isAnimationActive={false}
                    >
                      {totalsBar.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={getBarColor(entry.name, isDark)}
                        />
                      ))}
                    </Bar>
                  </RBarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Row 2: Daily Purchase Volume - 3 cols, 1 row */}
            <Card className="col-span-3 row-span-1 bg-card border-border flex flex-col">
              <CardHeader className="flex-shrink-0">
                <CardTitle className="text-foreground">Total Daily Purchase Volume</CardTitle>
              </CardHeader>
              <CardContent className="flex-1 min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                  <RLineChart data={totalPurchasesSeries}>
                    <CartesianGrid stroke={chartColors.grid} />
                    <XAxis
                      dataKey="label"
                      axisLine={{ stroke: chartColors.axis }}
                      tickLine={{ stroke: chartColors.axis }}
                      tick={{ fill: chartColors.axis, fontSize: 11 }}
                      height={40}
                      tickFormatter={(value) => {
                        if (!value) return '';
                        if (value.includes('/')) return value; // Already in MM/DD/YY format
                        return formatDateForInput(value);
                      }}
                    />
                    <YAxis
                      axisLine={{ stroke: chartColors.axis }}
                      tickLine={{ stroke: chartColors.axis }}
                      tick={{ fill: chartColors.axis, fontSize: 11 }}
                      width={50}
                      {...(() => {
                        const { domain, ticks } = calculateEvenYAxis(totalPurchasesSeries, 'value');
                        return {
                          domain,
                          ticks: ticks.length > 0 ? ticks : undefined
                        };
                      })()}
                    />
                    <Tooltip content={<CustomLineTooltip />} />
                    <Line
                      type="monotone"
                      dataKey="value"
                      name="Total Purchases"
                      stroke={chartColors.primary}
                      strokeWidth={3}
                      dot={false}
                      activeDot={{ r: 5 }}
                    />
                  </RLineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Row 3: Stockout Rate - full width (5 cols, 1 row) */}
            <Card className="col-span-5 row-span-1 bg-card border-border flex flex-col">
              <CardHeader className="flex-shrink-0">
                <CardTitle className="text-foreground">
                  Number of Stockouts
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                  <RLineChart data={stockoutSeries}>
                    <CartesianGrid stroke={chartColors.grid} strokeDasharray="3 3" />
                    <XAxis
                      dataKey="label"
                      axisLine={{ stroke: chartColors.axis }}
                      tickLine={{ stroke: chartColors.axis }}
                      tick={{ fill: chartColors.axis, fontSize: 11 }}
                      height={40}
                      tickFormatter={(value) => {
                        if (!value) return '';
                        if (value.includes('/')) return value; // Already in MM/DD/YY format
                        return formatDateForInput(value);
                      }}
                    />
                    <YAxis
                      axisLine={{ stroke: chartColors.axis }}
                      tickLine={{ stroke: chartColors.axis }}
                      tick={{ fill: chartColors.axis, fontSize: 11 }}
                      width={50}
                      {...(() => {
                        const { domain, ticks } = calculateEvenYAxis(stockoutSeries, 'value');
                        return {
                          domain,
                          ticks: ticks.length > 0 ? ticks : undefined
                        };
                      })()}
                    />
                    <Tooltip content={<CustomLineTooltip />} />
                    <Line
                      type="monotone"
                      dataKey="value"
                      name="Stockouts"
                      stroke={chartColors.primary}
                      strokeWidth={2.5}
                      dot={false}
                      activeDot={{ r: 4 }}
                    />
                  </RLineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

          </div>
        </div>
      </div>
    </div>
  );
}

