'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { useCamp, useRunForecast, useRunPlan } from '@/hooks/useGraphQL';
import Navbar from '@/components/Navbar';
import { format } from 'date-fns';

export default function CampDetailPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const campId = params.id as string;
  const [forecastLoading, setForecastLoading] = useState(false);
  const [planLoading, setPlanLoading] = useState(false);

  const { data, loading, error } = useCamp(campId, {
    skip: !isAuthenticated || !campId,
  });
  
  const camp = data?.camp;
  
  const [runForecast] = useRunForecast();
  const [runPlan] = useRunPlan();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  const formatDate = (dateStr: string) => {
    try {
      return format(new Date(dateStr), 'MMMM dd, yyyy HH:mm');
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <Link href="/camps" className="text-primary-600 hover:text-primary-700 flex items-center">
            <span className="mr-2">←</span> Back to Camps
          </Link>
        </div>

        {loading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading camp details...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-600">{error.message || 'An error occurred'}</p>
          </div>
        )}

        {!loading && !error && camp && (
          <div className="bg-white rounded-lg shadow-md p-8">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">{camp.name}</h1>
                <p className="text-lg text-gray-600 flex items-center">
                  <span className="mr-2">📍</span>
                  {camp.location}
                </p>
              </div>
              <Link
                href={`/camps/${campId}/activity`}
                className="px-4 py-2 bg-primary-600 text-white font-medium rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                View Activity Log
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Start Date & Time</h3>
                <p className="text-lg font-semibold text-gray-900">{formatDate(camp.start)}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">End Date & Time</h3>
                <p className="text-lg font-semibold text-gray-900">{formatDate(camp.end)}</p>
              </div>
            </div>

            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Requirements</h2>
              {camp.requirements.length === 0 ? (
                <p className="text-gray-500 italic">No requirements specified</p>
              ) : (
                <div className="space-y-3">
                  {camp.requirements.map((req, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200"
                    >
                      <div>
                        <h4 className="font-semibold text-gray-900">{req.role}</h4>
                        <p className="text-sm text-gray-600">Slot: {req.slot}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-primary-600">{req.count}</p>
                        <p className="text-xs text-gray-500">volunteers</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="mt-8 pt-6 border-t border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Actions</h2>
              <div className="flex flex-wrap gap-4">
                <button
                  onClick={async () => {
                    if (!campId) return;
                    setForecastLoading(true);
                    try {
                      await runForecast({ variables: { campId } });
                      alert('Forecast completed successfully!');
                    } catch (err: any) {
                      alert(`Forecast failed: ${err.message}`);
                    } finally {
                      setForecastLoading(false);
                    }
                  }}
                  disabled={forecastLoading}
                  className="px-6 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {forecastLoading ? 'Running Forecast...' : 'Run Forecast'}
                </button>
                <button
                  onClick={async () => {
                    if (!campId) return;
                    setPlanLoading(true);
                    try {
                      await runPlan({ variables: { campId } });
                      alert('Planning completed successfully!');
                    } catch (err: any) {
                      alert(`Planning failed: ${err.message}`);
                    } finally {
                      setPlanLoading(false);
                    }
                  }}
                  disabled={planLoading}
                  className="px-6 py-2 bg-green-600 text-white font-medium rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {planLoading ? 'Running Plan...' : 'Run Plan'}
                </button>
                <button className="px-6 py-2 bg-primary-600 text-white font-medium rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500">
                  Edit Camp
                </button>
                <button className="px-6 py-2 bg-white text-red-600 font-medium border border-red-600 rounded-md hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500">
                  Delete Camp
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

