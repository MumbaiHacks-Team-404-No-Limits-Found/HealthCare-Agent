'use client';

import React from 'react';
import { ActivityLog } from '@/lib/types';
import { format } from 'date-fns';

interface ActivityTimelineProps {
  activities: ActivityLog[];
}

export default function ActivityTimeline({ activities }: ActivityTimelineProps) {
  const formatTimestamp = (timestamp: string) => {
    try {
      return format(new Date(timestamp), 'MMM dd, yyyy HH:mm:ss');
    } catch {
      return timestamp;
    }
  };

  const getEventIcon = (event: string) => {
    if (event.includes('confirmed')) return '✅';
    if (event.includes('assignment')) return '📋';
    if (event.includes('planning') || event.includes('plan')) return '📊';
    if (event.includes('created')) return '🆕';
    if (event.includes('updated')) return '✏️';
    if (event.includes('deleted')) return '🗑️';
    if (event.includes('cancelled')) return '❌';
    return '📌';
  };

  const getEventColor = (event: string) => {
    if (event.includes('confirmed')) return 'bg-green-100 border-green-300';
    if (event.includes('cancelled') || event.includes('deleted')) return 'bg-red-100 border-red-300';
    if (event.includes('planning') || event.includes('plan')) return 'bg-blue-100 border-blue-300';
    if (event.includes('created')) return 'bg-purple-100 border-purple-300';
    if (event.includes('updated')) return 'bg-yellow-100 border-yellow-300';
    return 'bg-gray-100 border-gray-300';
  };

  if (activities.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p className="text-lg">No activity logs found</p>
        <p className="text-sm">Activity will appear here as actions are performed</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {activities.map((activity, idx) => (
        <div key={idx} className={`p-4 rounded-lg border-l-4 ${getEventColor(activity.event)}`}>
          <div className="flex items-start">
            <span className="text-2xl mr-3">{getEventIcon(activity.event)}</span>
            <div className="flex-1">
              <div className="flex justify-between items-start mb-2">
                <h4 className="text-sm font-semibold text-gray-900 capitalize">
                  {activity.event.replace(/_/g, ' ')}
                </h4>
                <span className="text-xs text-gray-500">
                  {formatTimestamp(activity.timestamp)}
                </span>
              </div>
              
              {activity.meta && Object.keys(activity.meta).length > 0 && (
                <div className="mt-2 space-y-1">
                  {Object.entries(activity.meta).map(([key, value]) => (
                    <div key={key} className="text-sm text-gray-700">
                      <strong className="capitalize">{key.replace(/_/g, ' ')}:</strong>{' '}
                      {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

