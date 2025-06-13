// lib/hooks.ts
import useSWR from 'swr';
const fetcher = (url: string) => fetch(url).then((r) => r.json());

export const useTxLog    = () => useSWR('/api/transactions?limit=200', fetcher, { refreshInterval: 60_000 });
export const usePipeline = () => useSWR('/api/pipeline', fetcher, { refreshInterval: 5 * 60_000 });
