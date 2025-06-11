import { NextRequest, NextResponse } from 'next/server';
import { pg } from '@/lib/db';

export async function GET(req: NextRequest) {
  const url = new URL(req.url);
  const since = url.searchParams.get('since');      // ISO timestamp
  const limit = Number(url.searchParams.get('limit') ?? 200);

  const { rows } = await pg.query(
    `
    SELECT *
    FROM fct_transactions
    WHERE transaction_ts >= COALESCE($1::timestamp, NOW() - INTERVAL '1 day')
    ORDER BY transaction_ts DESC
    LIMIT $2;
   `,
    [since, limit]
  );

  return NextResponse.json(rows);
}
