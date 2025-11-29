'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import Navbar from '@/components/Navbar';
import AssignmentCard from '@/components/AssignmentCard';
import AssignmentModal from '@/components/AssignmentModal';
import { campsApi, volunteersApi, assignmentsApi } from '@/lib/apiServices';
import { Camp, Volunteer, Assignment, AssignmentInput } from '@/lib/types';

export default function AssignmentsPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  
  const [camps, setCamps] = useState<Camp[]>([]);
  const [volunteers, setVolunteers] = useState<Volunteer[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCampId, setSelectedCampId] = useState<string>('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [campsData, volunteersData] = await Promise.all([
        campsApi.list(),
        volunteersApi.list(),
      ]);
      setCamps(campsData);
      setVolunteers(volunteersData);
      
      // Set first camp as default if available
      if (campsData.length > 0 && !selectedCampId) {
        setSelectedCampId(campsData[0].id);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const fetchAssignments = async (campId?: string) => {
    try {
      const params = campId ? { camp_id: campId } : {};
      const data = await assignmentsApi.list(params);
      setAssignments(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load assignments');
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (selectedCampId) {
      fetchAssignments(selectedCampId);
    }
  }, [selectedCampId]);

  const handleCreateAssignment = async (data: AssignmentInput) => {
    await assignmentsApi.create(data);
    await fetchAssignments(selectedCampId);
  };

  const handleUpdateStatus = async (assignmentId: string, status: string) => {
    try {
      await assignmentsApi.updateStatus(assignmentId, status);
      await fetchAssignments(selectedCampId);
    } catch (err: any) {
      alert(err.response?.data?.detail || err.message || 'Failed to update status');
    }
  };

  const handleDeleteAssignment = async (assignmentId: string) => {
    if (confirm('Are you sure you want to delete this assignment? This action cannot be undone.')) {
      try {
        await assignmentsApi.delete(assignmentId);
        await fetchAssignments(selectedCampId);
      } catch (err: any) {
        alert(err.response?.data?.detail || err.message || 'Failed to delete assignment');
      }
    }
  };

  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Create lookup maps
  const campMap = new Map(camps.map((c) => [c.id, c.name]));
  const volunteerMap = new Map(volunteers.map((v) => [v.id, v.name]));

  // Filter assignments by status
  const confirmedCount = assignments.filter((a) => a.status === 'confirmed').length;
  const assignedCount = assignments.filter((a) => a.status === 'assigned').length;
  const cancelledCount = assignments.filter((a) => a.status === 'cancelled').length;
  const backupCount = assignments.filter((a) => a.is_backup).length;

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Assignments</h1>
              <p className="text-gray-600">Manage volunteer assignments to camps</p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => fetchAssignments(selectedCampId)}
                className="px-4 py-2 bg-white text-blue-600 font-medium border border-blue-600 rounded-md hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Refresh
              </button>
              <button
                onClick={() => setIsModalOpen(true)}
                disabled={camps.length === 0 || volunteers.length === 0}
                className="px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span>Create Assignment</span>
              </button>
            </div>
          </div>
          
          {/* Camp Filter */}
          <div className="bg-white rounded-lg shadow p-4">
            <label htmlFor="camp-filter" className="block text-sm font-medium text-gray-700 mb-2">
              Filter by Camp:
            </label>
            <select
              id="camp-filter"
              value={selectedCampId}
              onChange={(e) => setSelectedCampId(e.target.value)}
              className="w-full md:w-96 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 bg-white"
            >
              {camps.length === 0 ? (
                <option value="">No camps available</option>
              ) : (
                <>
                  <option value="">All Camps</option>
                  {camps.map((camp) => (
                    <option key={camp.id} value={camp.id}>
                      {camp.name} - {camp.location}
                    </option>
                  ))}
                </>
              )}
            </select>
          </div>
        </div>

        {loading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading assignments...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-600">{error}</p>
          </div>
        )}

        {!loading && !error && (
          <>
            {/* Statistics Dashboard */}
            <div className="mb-6 bg-white rounded-lg shadow p-4">
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4 text-center">
                <div>
                  <p className="text-3xl font-bold text-blue-600">{assignments.length}</p>
                  <p className="text-sm text-gray-600">Total Assignments</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-green-600">{confirmedCount}</p>
                  <p className="text-sm text-gray-600">Confirmed</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-blue-600">{assignedCount}</p>
                  <p className="text-sm text-gray-600">Assigned</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-orange-600">{backupCount}</p>
                  <p className="text-sm text-gray-600">Backup</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-red-600">{cancelledCount}</p>
                  <p className="text-sm text-gray-600">Cancelled</p>
                </div>
              </div>
            </div>

            {assignments.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg shadow">
                <svg className="h-16 w-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                </svg>
                <p className="text-gray-500 text-lg font-medium">No assignments found</p>
                <p className="text-gray-400 text-sm mt-2">
                  {camps.length === 0 || volunteers.length === 0
                    ? 'Create camps and volunteers first, then create assignments'
                    : 'Create assignments to manage volunteer schedules'}
                </p>
                {camps.length > 0 && volunteers.length > 0 && (
                  <button
                    onClick={() => setIsModalOpen(true)}
                    className="mt-4 px-6 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700"
                  >
                    Create Your First Assignment
                  </button>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {assignments.map((assignment) => (
                  <AssignmentCard
                    key={assignment.id}
                    assignment={assignment}
                    campName={campMap.get(assignment.camp_id)}
                    volunteerName={volunteerMap.get(assignment.volunteer_id)}
                    onUpdateStatus={(status) => handleUpdateStatus(assignment.id, status)}
                    onDelete={() => handleDeleteAssignment(assignment.id)}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </div>

      <AssignmentModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleCreateAssignment}
        camps={camps}
        volunteers={volunteers}
      />
    </div>
  );
}
