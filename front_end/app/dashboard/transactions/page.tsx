"use client";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import { useEffect, useState } from "react";

interface Transaction {
  transaction_id: number;
  customer_id: number;
  order_value: number;
  date_purchased: Date;
  category: string;
}

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/transactions?limit=100")
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then((data: Transaction[]) => {
        setTransactions(data);
      })
      .catch((err) => {
        console.error(err);
        setError(err.message || "Failed to load");
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading transactions…</p>;
  if (error) return <p className="text-red-600">Error: {error}</p>;

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-4">Recent Transactions</h2>
      <div className="overflow-x-auto">
        <Table className="min-w-full table-auto border-collapse">
          <TableHeader>
            <TableRow>
              <TableHead className="px-4 py-2 border-b">ID</TableHead>
              <TableHead className="px-4 py-2 border-b">Customer_ID</TableHead>
              <TableHead className="px-4 py-2 border-b">Order_value</TableHead>
              <TableHead className="px-4 py-2 border-b">Date_purchased</TableHead>
              <TableHead className="px-4 py-2 border-b">Category</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {transactions.map((tx) => (
              <TableRow key={tx.transaction_id} className="hover:bg-gray-500">
                <TableCell className="px-4 py-2 border-b">{tx.transaction_id}</TableCell>
                <TableCell className="px-4 py-2 border-b">{tx.customer_id}</TableCell>
                <TableCell className="px-4 py-2 border-b">${tx.order_value.toFixed(2)}</TableCell>
                <TableCell className="px-4 py-2 border-b">
                  {new Date(tx.date_purchased).toLocaleDateString()}
                </TableCell>
                <TableCell className="px-4 py-2 border-b">{tx.category}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

