'use client';

import React, { useState } from 'react';
import { Assignment } from '@/lib/types';

interface AssignmentCardProps {
  assignment: Assignment;
  campName?: string;
  volunteerName?: string;
  onUpdateStatus?: (status: string) => void;
  onDelete?: () => void;
}

export default function AssignmentCard({
  assignment,
  campName,
  volunteerName,
  onUpdateStatus,
  onDelete,
}: AssignmentCardProps) {
  const [showStatusMenu, setShowStatusMenu] = useState(false);
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'confirmed':
        return 'bg-green-100 text-green-700';
      case 'assigned':
        return 'bg-blue-100 text-blue-700';
      case 'cancelled':
        return 'bg-red-100 text-red-700';
      case 'backup':
        return 'bg-yellow-100 text-yellow-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 hover:shadow-lg transition-shadow">
      <div className="p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              {assignment.role}
            </h3>
            {volunteerName && (
              <p className="text-sm text-gray-600">
                <strong>Volunteer:</strong> {volunteerName}
              </p>
            )}
            {campName && (
              <p className="text-sm text-gray-600">
                <strong>Camp:</strong> {campName}
              </p>
            )}
          </div>
          <div className="flex flex-col items-end space-y-2">
            <span className={`px-3 py-1 text-xs font-medium rounded-full ${getStatusColor(assignment.status)}`}>
              {assignment.status}
            </span>
            {assignment.is_backup && (
              <span className="px-3 py-1 text-xs font-medium bg-orange-100 text-orange-700 rounded-full">
                Backup
              </span>
            )}
          </div>
        </div>

        <div className="space-y-2 mb-4">
          <p className="text-sm text-gray-600">
            <strong>Slot:</strong> {assignment.slot}
          </p>
          <p className="text-xs text-gray-500">
            <strong>Assignment ID:</strong> {assignment.id}
          </p>
        </div>

        {(onUpdateStatus || onDelete) && (
          <div className="space-y-2">
            {onUpdateStatus && (
              <div className="relative">
                <button
                  onClick={() => setShowStatusMenu(!showStatusMenu)}
                  className="w-full px-4 py-2 text-sm font-medium text-blue-600 bg-white border border-blue-600 rounded-md hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  Change Status
                </button>
                {showStatusMenu && (
                  <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg">
                    {['assigned', 'confirmed', 'cancelled'].map((status) => (
                      <button
                        key={status}
                        onClick={() => {
                          onUpdateStatus(status);
                          setShowStatusMenu(false);
                        }}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 first:rounded-t-md last:rounded-b-md"
                      >
                        <span className="capitalize">{status}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
            {onDelete && (
              <button
                onClick={onDelete}
                className="w-full px-4 py-2 text-sm font-medium text-red-600 bg-white border border-red-600 rounded-md hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                Delete Assignment
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

