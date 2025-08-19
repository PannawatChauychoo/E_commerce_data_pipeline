
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
} from "recharts";

/* ---------- Color system ---------- */
const C = {
  bg: "#222831", // darkest (card/chart bg)
  grid: "#393E46", // subdued grid
  axis: "#DFD0B8", // light text/ticks
  accent1: "#FBBF24", // amber-400
  accent2: "#F97316", // orange-500
  accent3: "#EF4444", // red-500
  tipBg: "#393E46",
  tipBorder: "#948979",
};

type SimInputs = {
  days: number;
  total_customers_num: number;
  cust1_2_ratio: number;
  start_date: string; // ISO YYYY-MM-DD
  products_num: number;
};

type StepMetrics = {
  step: number;
  date: string;
  avgPurchasesCust1: number;
  avgPurchasesCust2: number;
  totalDailyPurchases: number;
  totalCustomers: number;
  totalProducts: number;
  stockoutRatePct: number;
};

/* ---------- Demo data (replace with Django later) ---------- */
function makeDemoPoint(prev: StepMetrics | undefined, step: number): StepMetrics {
  const base = prev ?? {
    step: 0,
    date: new Date().toISOString().slice(0, 10),
    avgPurchasesCust1: 0.6,
    avgPurchasesCust2: 0.4,
    totalDailyPurchases: 50,
    totalCustomers: 200,
    totalProducts: 300,
    stockoutRatePct: 1.5,
  };
  return {
    step,
    date: new Date(Date.now() + step * 86_400_000).toISOString().slice(0, 10),
    avgPurchasesCust1: Math.max(0, base.avgPurchasesCust1 + (Math.random() - 0.45) * 0.2),
    avgPurchasesCust2: Math.max(0, base.avgPurchasesCust2 + (Math.random() - 0.55) * 0.2),
    totalDailyPurchases: Math.max(0, Math.round(base.totalDailyPurchases + (Math.random() - 0.4) * 15)),
    totalCustomers: base.totalCustomers,
    totalProducts: base.totalProducts,
    stockoutRatePct: Math.max(0, Math.min(100, base.stockoutRatePct + (Math.random() - 0.5) * 2)),
  };
}

export default function SimulationWorkspace() {
  const [inputs, setInputs] = useState<SimInputs>({
    days: 7,
    total_customers_num: 200,
    cust1_2_ratio: 0.5,
    start_date: new Date().toISOString().slice(0, 10),
    products_num: 300,
  });

  const [running, setRunning] = useState(false);
  const [series, setSeries] = useState<StepMetrics[]>([]);
  const timerRef = useRef<NodeJS.Timer | null>(null);

  /* ---------- derived series ---------- */
  const avgPurchasesSeries = useMemo(
    () =>
      series.map((d) => ({
        label: d.date,
        cust1: d.avgPurchasesCust1,
        cust2: d.avgPurchasesCust2,
      })),
    [series]
  );

  const totalPurchasesSeries = useMemo(
    () => series.map((d) => ({ label: d.date, value: d.totalDailyPurchases })),
    [series]
  );

  const totalsBar = useMemo(() => {
    const last = series.at(-1);
    return [
      { name: "Customers", value: last?.totalCustomers ?? inputs.total_customers_num },
      { name: "Products", value: last?.totalProducts ?? inputs.products_num },
      { name: "Days", value: inputs.days },
    ];
  }, [series, inputs]);

  const stockoutSeries = useMemo(
    () => series.map((d) => ({ label: d.date, value: d.stockoutRatePct })),
    [series]
  );

  /* ---------- handlers ---------- */
  const onChange = (key: keyof SimInputs) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value;
    setInputs((s) => ({
      ...s,
      [key]:
        key === "start_date" ? v : key === "cust1_2_ratio" ? Number(v) : Number.parseInt(v, 10),
    }));
  };

  const stop = useCallback(() => {
    setRunning(false);
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = null;
  }, []);

  useEffect(() => () => stop(), [stop]);

  const start = async () => {
    setSeries([]);
    setRunning(true);
    // TODO: POST inputs to Django to kick off a run; capture run_id

    let step = 1;
    timerRef.current = setInterval(async () => {
      // TODO: Replace with polling Django endpoint for step metrics
      setSeries((prev) => [...prev, makeDemoPoint(prev.at(-1), step)]);
      step += 1;
      if (step > inputs.days) stop();
    }, 800);
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
      {/* Left panel: inputs */}
      <Card className="border-[#948979] bg-[#222831] lg:col-span-4 text-[#DFD0B8]">
        <CardHeader>
          <CardTitle className="text-lg">Simulation Inputs</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2">
            <Label htmlFor="start_date">Start Date</Label>
            <Input id="start_date" type="date" value={inputs.start_date} onChange={onChange("start_date")} className={inputClass} />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="days">Days</Label>
            <Input id="days" type="number" min={1} value={inputs.days} onChange={onChange("days")} className={inputClass} />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="total_customers_num">Total Customers</Label>
            <Input id="total_customers_num" type="number" min={1} value={inputs.total_customers_num} onChange={onChange("total_customers_num")} className={inputClass} />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="cust1_2_ratio">Cust1 : Cust2 Ratio (0–1)</Label>
            <Input id="cust1_2_ratio" type="number" step="0.05" min={0} max={1} value={inputs.cust1_2_ratio} onChange={onChange("cust1_2_ratio")} className={inputClass} />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="products_num">Product Per Category (34 total)</Label>
            <Input id="products_num" type="number" min={1} value={inputs.products_num} onChange={onChange("products_num")} className={inputClass} />
          </div>

          <div className="flex flex-col gap-3 pt-2">
            <Button onClick={start} disabled={running} className="w-full bg-[#DFD0B8] text-[#222831] hover:bg-[#FBBF24]/90">
              {running ? "Running…" : "Submit"}
            </Button>
            <Button onClick={stop} variant="secondary" disabled={!running} className="w-full bg-[#948979] text-black hover:bg-[#393E46]/30">
              Stop
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Right panel: charts */}
      <div className="lg:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Avg purchases per customer type */}
        <Card className="border-[#948979] bg-[#222831] text-[#DFD0B8]" style={{ ["--card-bg" as any]: C.bg, ["--card-fg" as any]: C.axis }}>
          <CardHeader><CardTitle>Average Purchases per Customer Type</CardTitle></CardHeader>
          <CardContent className="h-64 p-0">
            <div className="h-full w-full p-3">
              <ResponsiveContainer width="100%" height="100%">
                <RLineChart data={avgPurchasesSeries}>
                  <CartesianGrid stroke={C.grid} />
                  <XAxis dataKey="label" axisLine={{ stroke: C.axis }} tickLine={{ stroke: C.axis }} tick={{ fill: C.axis }} />
                  <YAxis axisLine={{ stroke: C.axis }} tickLine={{ stroke: C.axis }} tick={{ fill: C.axis }} />
                  <Tooltip {...tooltipProps} />
                  <Legend wrapperStyle={{ color: C.axis }} />
                  <Line type="monotone" dataKey="cust1" name="Cust1" stroke={C.accent1} strokeWidth={2.5} dot={false} />
                  <Line type="monotone" dataKey="cust2" name="Cust2" stroke={C.accent2} strokeWidth={2.5} dot={false} />
                </RLineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Total daily purchases */}
        <Card className="border-[#948979] bg-[#222831] text-[#DFD0B8]" style={{ ["--card-bg" as any]: C.bg, ["--card-fg" as any]: C.axis }}>
          <CardHeader><CardTitle>Total Daily Purchases</CardTitle></CardHeader>
          <CardContent className="h-64 p-0">
            <div className="h-full w-full p-3">
              <ResponsiveContainer width="100%" height="100%">
                <RLineChart data={totalPurchasesSeries}>
                  <CartesianGrid stroke={C.grid} />
                  <XAxis dataKey="label" axisLine={{ stroke: C.axis }} tickLine={{ stroke: C.axis }} tick={{ fill: C.axis }} />
                  <YAxis axisLine={{ stroke: C.axis }} tickLine={{ stroke: C.axis }} tick={{ fill: C.axis }} />
                  <Tooltip {...tooltipProps} />
                  <Line type="monotone" dataKey="value" name="Purchases" stroke={C.accent3} strokeWidth={2.5} dot={false} />
                </RLineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Totals bar chart */}
        <Card className="border-[#948979] bg-[#222831] text-[#DFD0B8]" style={{ ["--card-bg" as any]: C.bg, ["--card-fg" as any]: C.axis }}>
          <CardHeader><CardTitle>Total Count (Customers / Products / Days)</CardTitle></CardHeader>
          <CardContent className="h-64 p-0">
            <div className="h-full w-full p-3">
              <ResponsiveContainer width="100%" height="100%">
                <RBarChart data={totalsBar}>
                  <CartesianGrid stroke={C.grid} />
                  <XAxis dataKey="name" axisLine={{ stroke: C.axis }} tickLine={{ stroke: C.axis }} tick={{ fill: C.axis }} />
                  <YAxis axisLine={{ stroke: C.axis }} tickLine={{ stroke: C.axis }} tick={{ fill: C.axis }} />
                  <Tooltip {...tooltipProps} />
                  <Bar dataKey="value" name="Total" fill={C.accent1} fillOpacity={0.9} />
                </RBarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Stockout Rate */}
        <Card className="border-[#948979] bg-[#222831] text-[#DFD0B8]" style={{ ["--card-bg" as any]: C.bg, ["--card-fg" as any]: C.axis }}>
          <CardHeader><CardTitle>Stockout Rate (%)</CardTitle></CardHeader>
          <CardContent className="h-64 p-0">
            <div className="h-full w-full p-3">
              <ResponsiveContainer width="100%" height="100%">
                <RLineChart data={stockoutSeries}>
                  <CartesianGrid stroke={C.grid} />
                  <XAxis dataKey="label" axisLine={{ stroke: C.axis }} tickLine={{ stroke: C.axis }} tick={{ fill: C.axis }} />
                  <YAxis axisLine={{ stroke: C.axis }} tickLine={{ stroke: C.axis }} tick={{ fill: C.axis }} />
                  <Tooltip {...tooltipProps} />
                  <Line type="monotone" dataKey="value" name="Stockout %" stroke={C.accent2} strokeWidth={2.5} dot={false} />
                </RLineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </div >
  );
}

