'use client';

import React from 'react';
import { Volunteer } from '@/lib/types';

interface VolunteerCardProps {
  volunteer: Volunteer;
  onEdit?: () => void;
  onDelete?: () => void;
}

export default function VolunteerCard({ volunteer, onEdit, onDelete }: VolunteerCardProps) {
  // Handle both REST API (no_show_rate) and GraphQL (noShowRate) field names
  const noShowRate = (volunteer as any).noShowRate ?? (volunteer as any).no_show_rate ?? 0;
  const noShowPercentage = Math.round(noShowRate * 100);

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 hover:shadow-lg transition-shadow">
      <div className="p-6">
        <div className="flex justify-between items-start mb-4">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center text-primary-600 font-bold text-xl mr-3">
              {volunteer.name.charAt(0).toUpperCase()}
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{volunteer.name}</h3>
              <p className="text-sm text-gray-600">{volunteer.phone}</p>
            </div>
          </div>
          <span
            className={`px-3 py-1 text-xs font-medium rounded-full ${
              noShowPercentage < 20
                ? 'bg-green-100 text-green-700'
                : noShowPercentage < 40
                ? 'bg-yellow-100 text-yellow-700'
                : 'bg-red-100 text-red-700'
            }`}
          >
            {noShowPercentage}% no-show
          </span>
        </div>

        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Skills:</h4>
          <div className="flex flex-wrap gap-2">
            {volunteer.skills.length > 0 ? (
              volunteer.skills.map((skill, idx) => (
                <span
                  key={idx}
                  className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded"
                >
                  {skill}
                </span>
              ))
            ) : (
              <span className="text-sm text-gray-500 italic">No skills listed</span>
            )}
          </div>
        </div>

        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Availability:</h4>
          {volunteer.availability.length > 0 ? (
            <div className="space-y-1">
              {volunteer.availability.slice(0, 2).map((avail, idx) => (
                <div key={idx} className="text-sm text-gray-600">
                  <strong>{avail.date}:</strong> {avail.slots.join(', ')}
                </div>
              ))}
              {volunteer.availability.length > 2 && (
                <p className="text-xs text-gray-500 italic">
                  +{volunteer.availability.length - 2} more dates
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-500 italic">No availability set</p>
          )}
        </div>

        {(onEdit || onDelete) && (
          <div className="flex space-x-2">
            {onEdit && (
              <button
                onClick={onEdit}
                className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                Edit
              </button>
            )}
            {onDelete && (
              <button
                onClick={onDelete}
                className="flex-1 px-4 py-2 text-sm font-medium text-red-600 bg-white border border-red-600 rounded-md hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                Delete
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

