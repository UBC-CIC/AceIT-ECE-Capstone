interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

const DEFAULT_TTL = 5 * 60 * 1000; // 5 minutes default cache duration
const cache = new Map<string, CacheEntry<any>>();

export const getCachedData = <T>(key: string): T | null => {
  const entry = cache.get(key);
  if (!entry) return null;

  const now = Date.now();
  if (now - entry.timestamp > DEFAULT_TTL) {
    cache.delete(key);
    return null;
  }

  return entry.data as T;
};

export const setCachedData = <T>(key: string, data: T): void => {
  cache.set(key, {
    data,
    timestamp: Date.now(),
  });
};

export const clearCache = (): void => {
  cache.clear();
};
