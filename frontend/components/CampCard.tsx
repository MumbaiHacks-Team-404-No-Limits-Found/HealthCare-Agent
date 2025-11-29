'use client';

import React from 'react';
import Link from 'next/link';
import { Camp } from '@/lib/types';
import { format } from 'date-fns';

interface CampCardProps {
  camp: Camp;
  onEdit?: () => void;
  onDelete?: () => void;
}

export default function CampCard({ camp, onEdit, onDelete }: CampCardProps) {
  const formatDate = (dateStr: string) => {
    try {
      return format(new Date(dateStr), 'MMM dd, yyyy');
    } catch {
      return dateStr;
    }
  };

  const totalRequirements = camp.requirements.reduce((sum, req) => sum + req.count, 0);

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 hover:shadow-lg transition-shadow">
      <div className="p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">{camp.name}</h3>
            <p className="text-gray-600 flex items-center">
              <span className="mr-2">📍</span>
              {camp.location}
            </p>
          </div>
          <span className="px-3 py-1 text-sm font-medium bg-primary-100 text-primary-700 rounded-full">
            Active
          </span>
        </div>

        <div className="mb-4 space-y-2">
          <p className="text-sm text-gray-600 flex items-center">
            <span className="mr-2">📅</span>
            <strong className="mr-1">Start:</strong> {formatDate(camp.start)}
          </p>
          <p className="text-sm text-gray-600 flex items-center">
            <span className="mr-2">🏁</span>
            <strong className="mr-1">End:</strong> {formatDate(camp.end)}
          </p>
        </div>

        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Requirements:</h4>
          <div className="space-y-1">
            {camp.requirements.slice(0, 3).map((req, idx) => (
              <div key={idx} className="text-sm text-gray-600">
                • {req.count}x {req.role} ({req.slot})
              </div>
            ))}
            {camp.requirements.length > 3 && (
              <div className="text-sm text-gray-500 italic">
                +{camp.requirements.length - 3} more...
              </div>
            )}
          </div>
          <p className="text-sm font-medium text-gray-700 mt-2">
            Total volunteers needed: {totalRequirements}
          </p>
        </div>

        <div className="space-y-2">
          <div className="flex space-x-2">
            <Link
              href={`/camps/${camp.id}`}
              className="flex-1 px-4 py-2 text-center text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              View Details
            </Link>
            <Link
              href={`/camps/${camp.id}/activity`}
              className="flex-1 px-4 py-2 text-center text-sm font-medium text-blue-600 bg-white border border-blue-600 rounded-md hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Activity
            </Link>
          </div>
          
          {(onEdit || onDelete) && (
            <div className="flex space-x-2">
              {onEdit && (
                <button
                  onClick={onEdit}
                  className="flex-1 px-4 py-2 text-center text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
                >
                  Edit
                </button>
              )}
              {onDelete && (
                <button
                  onClick={onDelete}
                  className="flex-1 px-4 py-2 text-center text-sm font-medium text-red-600 bg-white border border-red-600 rounded-md hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  Delete
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

