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


/* ---------- Updated Color system using CSS custom properties ---------- */
const getChartColors = () => {
  if (typeof window === 'undefined') return {};
  const style = getComputedStyle(document.documentElement);
  return {
    bg: `hsl(${style.getPropertyValue('--card')})`,
    grid: `hsl(${style.getPropertyValue('--border')})`,
    axis: `hsl(${style.getPropertyValue('--foreground')})`,
    accent1: `hsl(${style.getPropertyValue('--chart-1')})`,
    accent2: `hsl(${style.getPropertyValue('--chart-2')})`,
    accent3: `hsl(${style.getPropertyValue('--chart-3')})`,
    tipBg: `hsl(${style.getPropertyValue('--popover')})`,
    tipBorder: `hsl(${style.getPropertyValue('--border')})`,
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
  cust1_avg_purchase: number;
  cust2_avg_purchase: number;
  total_daily_purchases: number;
  total_cust1: number;
  total_cust2: number;
  total_products: number;
  stockout_rate: number;
};


// Choosing colors for barchart using CSS custom properties
const getBarColor = (name: string) => {
  const colors = getChartColors();
  switch (name) {
    case "Customers1":
      return colors.accent2;
    case "Customers2":
      return colors.accent3;
    case "Products":
      return colors.accent1;
    default:
      return colors.accent1;
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

// Convert YYYYMMDD to YYYY-MM-DD
function formatDateForInput(dateStr: string): string {
  if (dateStr.length === 8) {
    return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`;
  }
  return dateStr;
}

/* ---------- Component ---------- */
export default function SimulationWorkspace() {
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

  /* Timers */
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const labelRef = useRef<ReturnType<typeof setInterval> | null>(null);

  /* Chart container ref for auto-scroll */
  const chartContainerRef = useRef<HTMLDivElement>(null);
  /* Sidebar ref to measure height */
  const sidebarRef = useRef<HTMLDivElement>(null);
  /* State to track sidebar height */
  const [sidebarHeight, setSidebarHeight] = useState<number>(0);

  /* Error handler */
  const errRef = useRef<HTMLDivElement>(null);
  const debugRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (errRef.current) errRef.current.scrollTop = errRef.current.scrollHeight;
  }, [errorMsg]);

  useEffect(() => {
    if (debugRef.current) debugRef.current.scrollTop = debugRef.current.scrollHeight;
  }, [series.length, runId]);

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


  /* Derived series for charts */
  const avgPurchasesSeries = useMemo(
    () =>
      series.map((d) => ({
        label: addDays(inputs.start_date, Math.max(0, (d.step ?? 1) - 1)),
        cust1: Number(d.cust1_avg_purchase ?? 0),
        cust2: Number(d.cust2_avg_purchase ?? 0),
      })),
    [series, inputs.start_date]
  );

  const totalPurchasesSeries = useMemo(
    () =>
      series.map((d) => ({
        label: addDays(inputs.start_date, Math.max(0, (d.step ?? 1) - 1)),
        value: Number(d.total_daily_purchases ?? 0),
      })),
    [series, inputs.start_date]
  );

  const stockoutSeries = useMemo(
    () =>
      series.map((d) => ({
        label: addDays(inputs.start_date, Math.max(0, (d.step ?? 1) - 1)),
        value: Number(d.stockout_rate ?? 0),
      })),
    [series, inputs.start_date]
  );

  const totalsBar = useMemo(() => {
    const last = series.at(-1);
    const totalCustomers1 = Number(last?.total_cust1 ?? 0)
    const totalCustomers2 = Number(last?.total_cust2 ?? 0);
    const totalProducts = Number(last?.total_products ?? inputs.n_products_per_category);
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
    setRunId(null);
    setElapsed(0);
    setRunning(false);
    setSeries([]);
    setErrorMsg(null);
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
    };

    // derive max steps from either max_steps or days
    const maxSteps = Number(payload.max_steps ?? 0);

    // ---- Kick off backend run
    try {
      const csrf = getCSRFCookie();
      const res = await fetch("http://localhost:8000/api/simulate/", {
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
          const r = await fetch(`http://localhost:8000/api/simulate/${run_id}?since=${since}`, {
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
            if (error) setErrorMsg(error);
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
  const inputClass = "bg-input border-border text-foreground placeholder:text-muted-foreground focus-visible:ring-ring focus-visible:ring-2 focus-visible:ring-offset-0";

  const chartColors = getChartColors();
  const tooltipProps = {
    contentStyle: {
      backgroundColor: chartColors.tipBg,
      borderColor: chartColors.tipBorder,
      color: chartColors.axis,
      borderRadius: '8px',
      border: '1px solid'
    },
    labelStyle: { color: chartColors.axis },
    itemStyle: { color: chartColors.axis },
  } as const;

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
                <span className="text-sm font-medium text-primary">{inputs.n_customers1}</span>
              </div>
              <Slider
                value={[inputs.n_customers1]}
                onValueChange={onSliderChange("n_customers1")}
                min={0}
                max={5000}
                step={10}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>0</span>
                <span>5,000</span>
              </div>
            </div>

            {/* Type 2 Customers Slider */}
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <Label className="text-sm font-medium text-foreground">Type 2 Customers</Label>
                <span className="text-sm font-medium text-primary">{inputs.n_customers2}</span>
              </div>
              <Slider
                value={[inputs.n_customers2]}
                onValueChange={onSliderChange("n_customers2")}
                min={0}
                max={5000}
                step={10}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>0</span>
                <span>5,000</span>
              </div>
            </div>

            {/* Products Per Category Slider */}
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <Label className="text-sm font-medium text-foreground">Products Per Category</Label>
                <span className="text-sm font-medium text-primary">{inputs.n_products_per_category}</span>
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
                  "Start Simulation"
                )}
              </Button>

              <Button
                onClick={reset}
                variant="outline"
                disabled={!running && series.length === 0}
                className="w-full"
              >
                Reset
              </Button>

              {/* Status info - more subtle */}
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
                  Steps: {series.length} / {inputs.max_steps}
                </div>
              </div>


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
                <CardTitle className="text-foreground">Average Purchases by Customer Type</CardTitle>
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
                    />
                    <YAxis
                      axisLine={{ stroke: chartColors.axis, strokeWidth: 1 }}
                      tickLine={{ stroke: chartColors.axis, strokeWidth: 1 }}
                      tick={{ fill: chartColors.axis, fontSize: 11 }}
                      width={40}
                    />
                    <Tooltip {...tooltipProps} />
                    <Legend wrapperStyle={{ color: chartColors.axis, fontSize: '12px' }} />
                    <Line
                      type="monotone"
                      dataKey="cust1"
                      name="Type 1"
                      stroke={chartColors.accent1}
                      strokeWidth={2.5}
                      dot={false}
                      activeDot={{ r: 4 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="cust2"
                      name="Type 2"
                      stroke={chartColors.accent2}
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
                    <Tooltip {...tooltipProps} />
                    <Bar dataKey="value" name="Count" fillOpacity={0.8} radius={[4, 4, 0, 0]}>
                      {totalsBar.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={getBarColor(entry.name)} />
                      ))}
                    </Bar>
                  </RBarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Row 2: Daily Purchase Volume - 3 cols, 1 row */}
            <Card className="col-span-3 row-span-1 bg-card border-border flex flex-col">
              <CardHeader className="flex-shrink-0">
                <CardTitle className="text-foreground">Daily Purchase Volume</CardTitle>
              </CardHeader>
              <CardContent className="flex-1 min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                  <RLineChart data={totalPurchasesSeries}>
                    <CartesianGrid stroke={chartColors.grid} strokeDasharray="3 3" />
                    <XAxis
                      dataKey="label"
                      axisLine={{ stroke: chartColors.axis }}
                      tickLine={{ stroke: chartColors.axis }}
                      tick={{ fill: chartColors.axis, fontSize: 11 }}
                      height={40}
                    />
                    <YAxis
                      axisLine={{ stroke: chartColors.axis }}
                      tickLine={{ stroke: chartColors.axis }}
                      tick={{ fill: chartColors.axis, fontSize: 11 }}
                      width={50}
                    />
                    <Tooltip {...tooltipProps} />
                    <Line
                      type="monotone"
                      dataKey="value"
                      name="Total Purchases"
                      stroke={chartColors.accent2}
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
                <CardTitle className="text-foreground">Stockout Rate (%)</CardTitle>
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
                    />
                    <YAxis
                      axisLine={{ stroke: chartColors.axis }}
                      tickLine={{ stroke: chartColors.axis }}
                      tick={{ fill: chartColors.axis, fontSize: 11 }}
                      width={50}
                    />
                    <Tooltip {...tooltipProps} />
                    <Line
                      type="monotone"
                      dataKey="value"
                      name="Stockout %"
                      stroke={chartColors.accent3}
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

