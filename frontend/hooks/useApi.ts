'use client';

import { useState } from 'react';
import api from '@/lib/api';

interface UseApiResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  execute: (endpoint: string, method?: string, body?: any) => Promise<T | null>;
}

export function useApi<T = any>(): UseApiResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = async (
    endpoint: string,
    method: string = 'GET',
    body: any = null
  ): Promise<T | null> => {
    setLoading(true);
    setError(null);

    try {
      let response;
      switch (method.toUpperCase()) {
        case 'GET':
          response = await api.get(endpoint);
          break;
        case 'POST':
          response = await api.post(endpoint, body);
          break;
        case 'PUT':
          response = await api.put(endpoint, body);
          break;
        case 'DELETE':
          response = await api.delete(endpoint);
          break;
        case 'PATCH':
          response = await api.patch(endpoint, body);
          break;
        default:
          response = await api.get(endpoint);
      }
      setData(response.data);
      return response.data;
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'An error occurred';
      setError(errorMsg);
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, execute };
}

