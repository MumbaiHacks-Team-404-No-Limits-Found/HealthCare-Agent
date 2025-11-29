'use client';

import React, { useEffect, useMemo } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { useCamp, useCampActivity } from '@/hooks/useGraphQL';
import Navbar from '@/components/Navbar';
import ActivityTimeline from '@/components/ActivityTimeline';

export default function CampActivityPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const campId = params.id as string;

  const { data: campData, loading: campLoading } = useCamp(campId, {
    skip: !isAuthenticated || !campId,
  });
  
  const { data: activityData, loading: activitiesLoading, error, refetch } = useCampActivity(
    campId,
    {
      skip: !isAuthenticated || !campId,
    }
  );
  
  const camp = campData?.camp;
  
  // Transform GraphQL activity data to match ActivityTimeline component expectations
  const activities = useMemo(() => {
    if (!activityData?.campActivity) return [];
    
    return activityData.campActivity.map((log) => {
      // Parse meta string to object if it's a string
      let meta: Record<string, any> = {};
      try {
        if (typeof log.meta === 'string') {
          meta = JSON.parse(log.meta);
        } else {
          meta = log.meta || {};
        }
      } catch {
        // If parsing fails, use the string as a value
        meta = { raw: log.meta };
      }
      
      return {
        timestamp: log.timestamp,
        event: log.event,
        meta,
      };
    });
  }, [activityData]);

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

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6 flex justify-between items-center">
          <Link href={`/camps/${campId}`} className="text-primary-600 hover:text-primary-700 flex items-center">
            <span className="mr-2">←</span> Back to Camp Details
          </Link>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-primary-600 text-white font-medium rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            Refresh
          </button>
        </div>

        {campLoading ? (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <div className="animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-1/3 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-1/4"></div>
            </div>
          </div>
        ) : camp ? (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">{camp.name}</h1>
            <p className="text-gray-600 flex items-center">
              <span className="mr-2">📍</span>
              {camp.location}
            </p>
          </div>
        ) : null}

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">Activity Timeline</h2>

          {activitiesLoading && (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading activity logs...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-600">{error.message || 'An error occurred'}</p>
            </div>
          )}

          {!activitiesLoading && !error && activities.length > 0 && (
            <ActivityTimeline activities={activities} />
          )}
          
          {!activitiesLoading && !error && activities.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <p className="text-lg">No activity logs found</p>
              <p className="text-sm">Activity will appear here as actions are performed</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

