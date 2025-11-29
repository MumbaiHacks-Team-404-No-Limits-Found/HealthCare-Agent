'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';

interface UseFetchOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  body?: any;
  skip?: boolean;
}

interface UseFetchResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useFetch<T = any>(
  url: string,
  options: UseFetchOptions = {}
): UseFetchResult<T> {
  const { method = 'GET', body = null, skip = false } = options;
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(!skip);
  const [error, setError] = useState<string | null>(null);
  const [refetchTrigger, setRefetchTrigger] = useState(0);

  const fetchData = async () => {
    if (skip) return;

    setLoading(true);
    setError(null);

    try {
      let response;
      switch (method) {
        case 'GET':
          response = await api.get(url);
          break;
        case 'POST':
          response = await api.post(url, body);
          break;
        case 'PUT':
          response = await api.put(url, body);
          break;
        case 'DELETE':
          response = await api.delete(url);
          break;
        case 'PATCH':
          response = await api.patch(url, body);
          break;
        default:
          response = await api.get(url);
      }
      setData(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [url, method, JSON.stringify(body), refetchTrigger, skip]);

  const refetch = () => {
    setRefetchTrigger((prev) => prev + 1);
  };

  return { data, loading, error, refetch };
}

