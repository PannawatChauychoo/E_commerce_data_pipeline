import { NextRequest, NextResponse } from 'next/server';
import { pg_pool } from '@/lib/db';

export async function GET(req: NextRequest) {
  const url = new URL(req.url);
  const limit = Number(url.searchParams.get('limit') ?? 50);

  const { rows } = await pg_pool.query(
    `
    SELECT transaction_id, unique_id as customer_id, (unit_price * quantity) as order_value, date_purchased::date, category
    FROM walmart.transactions
    ORDER BY date_purchased DESC
    LIMIT $1;
   `,
    [limit]
  );

  return NextResponse.json(rows);
}
