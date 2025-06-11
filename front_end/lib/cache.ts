// lib/cache.ts
import IORedis from 'ioredis';
export const redis =
  process.env.REDIS_URL ? new IORedis(process.env.REDIS_URL) : null;
