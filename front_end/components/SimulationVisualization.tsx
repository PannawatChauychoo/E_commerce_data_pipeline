// SimulationVisualization.tsx
"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
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


/* ---------- Color system ---------- */
const C = {
  bg: "#222831",    // darkest (card/chart bg)
  grid: "#393E46",  // subdued grid
  axis: "#DFD0B8",  // light text/ticks
  accent1: "#FBBF24", // amber-400
  accent2: "#F97316", // orange-500
  accent3: "#EF4444", // red-500
  tipBg: "#393E46",
  tipBorder: "#948979",
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


// Choosing colors for barchart
const getBarColor = (name: string) => {
  switch (name) {
    case "Customers1":
      return C.accent2; // "#F97316" - Orange-500
    case "Customers2":
      return C.accent3; // "#EF4444" - Red-500
    case "Products":
      return C.accent1; // "#FBBF24" - Amber-400
    default:
      return C.accent1; // Fallback to amber
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


  /* Error handler */
  const errRef = useRef<HTMLDivElement>(null);
  const debugRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (errRef.current) errRef.current.scrollTop = errRef.current.scrollHeight;
  }, [errorMsg]);

  useEffect(() => {
    if (debugRef.current) debugRef.current.scrollTop = debugRef.current.scrollHeight;
  }, [series.length, runId]);


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

  /* Input handler */
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
  const inputClass =
    "bg-[#393E46] border-[#948979] text-[#DFD0B8] placeholder:text-[#DFD0B8]/60 focus-visible:ring-[#FBBF24] focus-visible:ring-2";

  const tooltipProps = {
    contentStyle: { backgroundColor: C.tipBg, borderColor: C.tipBorder, color: C.axis },
    labelStyle: { color: C.axis },
    itemStyle: { color: C.axis },
  } as const;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 py-6">
      {/* Left panel: inputs + controls */}
      <Card className="border-[#948979] bg-[#222831] lg:col-span-4 text-[#DFD0B8]">
        <CardHeader>
          <CardTitle className="text-lg">Simulation Inputs</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2">
            <Label htmlFor="start_date">Start Date</Label>
            <Input
              id="start_date"
              type="date"
              value={inputs.start_date}
              onChange={onChange("start_date")}
              className={inputClass}
            />
            <small className="text-xs text-gray-400">
              Will be sent as: {formatDateForAPI(inputs.start_date)}
            </small>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="days">Days</Label>
            <Input
              id="days"
              type="number"
              min={1}
              value={inputs.max_steps}
              onChange={onChange("max_steps")}
              className={inputClass}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="n_customers1">Total Customers (type 1)</Label>
            <Input
              id="n_customers1"
              type="number"
              min={1}
              value={inputs.n_customers1}
              onChange={onChange("n_customers1")}
              className={inputClass}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="n_customers2">Total Customers (type 2)</Label>
            <Input
              id="n_customers2"
              type="number"
              min={1}
              value={inputs.n_customers2}
              onChange={onChange("n_customers2")}
              className={inputClass}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="n_products_per_category">Product Per Category (34 total category)</Label>
            <Input
              id="n_products_per_category"
              type="number"
              min={1}
              value={inputs.n_products_per_category}
              onChange={onChange("n_products_per_category")}
              className={inputClass}
            />
          </div>

          <div className="flex flex-col gap-3 pt-2">
            <Button
              onClick={start}
              disabled={running}
              className="w-full bg-[#DFD0B8] text-[#222831] hover:bg-[#FBBF24]/90"
            >
              {running ? `Running… ${fmtElapsed(elapsed)}` : "Submit"}
            </Button>

            <Button
              onClick={reset}
              variant="secondary"
              disabled={!running && series.length === 0}
              className="w-full bg-[#948979] text-black hover:bg-[#393E46]/30"
            >
              Reset
            </Button>

            {/* Debug info */}
            <div className="bg-green-900/20 border border-green-500/50 rounded p-3 text-xs h-40 overflow-y-auto overscroll-contain"
              ref={debugRef}>
              <p className="text-green-300 font-medium top-0 bg-green-900/30 py-1">
                Debug Info:
              </p>
              <div className="space-y-1 text-green-200 mt-2">
                <p>API URL: /api/simulate/</p>
                <p>Run ID: {runId || "None"}</p>
                <p>Steps received: {series.length}</p>
                {/* Optional: stream recent lines */}
                {series.slice(-200).map((m, i) => (
                  <p key={i} className="whitespace-pre-wrap break-words">
                    {JSON.stringify(m)}
                  </p>
                ))}
              </div>

            </div>


          </div>
        </CardContent>
      </Card>

      {/* Right panel: charts */}
      <div className="lg:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Avg purchases per customer type */}
        <Card
          className="border-[#948979] bg-[#222831] text-[#DFD0B8]"
          style={{ ["--card-bg" as any]: C.bg, ["--card-fg" as any]: C.axis }}
        >
          <CardHeader>
            <CardTitle>Average Purchases per Customer Type</CardTitle>
          </CardHeader>
          <CardContent className="h-full w-full pt-4">
            <ResponsiveContainer width="100%" height="90%">
              <RLineChart data={avgPurchasesSeries}>
                <CartesianGrid stroke={C.grid} />
                <XAxis
                  dataKey="label"
                  axisLine={{ stroke: C.axis, strokeWidth: 1 }}
                  tickLine={{ stroke: C.axis, strokeWidth: 1 }}
                  tick={{ fill: C.axis, fontSize: 12 }}
                  height={60}
                />
                <YAxis
                  axisLine={{ stroke: C.axis, strokeWidth: 1 }}
                  tickLine={{ stroke: C.axis, strokeWidth: 1 }}
                  tick={{ fill: C.axis, fontSize: 12 }}
                  width={60}
                />
                <Tooltip {...tooltipProps} />
                <Legend wrapperStyle={{ color: C.axis }} />
                <Line type="monotone" dataKey="cust1" name="Customers1" stroke={C.accent1} strokeWidth={2.5} dot={false} />
                <Line type="monotone" dataKey="cust2" name="Customers2" stroke={C.accent2} strokeWidth={2.5} dot={false} />
              </RLineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Total daily purchases */}
        <Card
          className="border-[#948979] bg-[#222831] text-[#DFD0B8]"
          style={{ ["--card-bg" as any]: C.bg, ["--card-fg" as any]: C.axis }}
        >
          <CardHeader>
            <CardTitle>Total Daily Purchases</CardTitle>
          </CardHeader>
          <CardContent className="h-full w-full pt-4">
            <ResponsiveContainer width="100%" height="90%">
              <RLineChart data={totalPurchasesSeries}>
                <CartesianGrid stroke={C.grid} />
                <XAxis
                  dataKey="label"
                  axisLine={{ stroke: C.axis }}
                  tickLine={{ stroke: C.axis }}
                  tick={{ fill: C.axis }}
                />
                <YAxis
                  axisLine={{ stroke: C.axis }}
                  tickLine={{ stroke: C.axis }}
                  tick={{ fill: C.axis }}
                />
                <Tooltip {...tooltipProps} />
                <Line type="monotone" dataKey="value" name="Total Purchases" stroke={C.accent2} strokeWidth={2.5} dot={false} />
              </RLineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Totals bar chart */}
        <Card
          className="border-[#948979] bg-[#222831] text-[#DFD0B8]"
          style={{ ["--card-bg" as any]: C.bg, ["--card-fg" as any]: C.axis }}
        >
          <CardHeader>
            <CardTitle>Total Count (Customers / Products)</CardTitle>
          </CardHeader>
          <CardContent className="h-full w-full pt-4">
            <ResponsiveContainer width="100%" height="90%">
              <RBarChart data={totalsBar}>
                <CartesianGrid stroke={C.grid} />
                <XAxis
                  dataKey="name"
                  axisLine={{ stroke: C.axis }}
                  tickLine={{ stroke: C.axis }}
                  tick={{ fill: C.axis }}
                />
                <YAxis
                  axisLine={{ stroke: C.axis }}
                  tickLine={{ stroke: C.axis }}
                  tick={{ fill: C.axis }}
                />
                <Tooltip {...tooltipProps} />
                <Bar dataKey="value" name="Total" fillOpacity={0.9}>
                  {totalsBar.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getBarColor(entry.name)} />
                  ))}
                </Bar>
              </RBarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Stockout Rate */}
        <Card
          className="border-[#948979] bg-[#222831] text-[#DFD0B8]"
          style={{ ["--card-bg" as any]: C.bg, ["--card-fg" as any]: C.axis }}
        >
          <CardHeader>
            <CardTitle>Stockout Rate (%)</CardTitle>
          </CardHeader>
          <CardContent className="h-full w-full pt-4">
            <ResponsiveContainer width="100%" height="90%">
              <RLineChart data={stockoutSeries}>
                <CartesianGrid stroke={C.grid} />
                <XAxis
                  dataKey="label"
                  axisLine={{ stroke: C.axis }}
                  tickLine={{ stroke: C.axis }}
                  tick={{ fill: C.axis }}
                />
                <YAxis
                  axisLine={{ stroke: C.axis }}
                  tickLine={{ stroke: C.axis }}
                  tick={{ fill: C.axis }}
                />
                <Tooltip {...tooltipProps} />
                <Line type="monotone" dataKey="value" name="Stockout %" stroke={C.accent2} strokeWidth={2.5} dot={false} />
              </RLineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div >
  );
}

