'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import Navbar from '@/components/Navbar';
import VolunteerCard from '@/components/VolunteerCard';
import VolunteerModal from '@/components/VolunteerModal';
import { volunteersApi } from '@/lib/apiServices';
import { Volunteer, VolunteerInput } from '@/lib/types';

export default function VolunteersPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [volunteers, setVolunteers] = useState<Volunteer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingVolunteer, setEditingVolunteer] = useState<Volunteer | null>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  const fetchVolunteers = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await volunteersApi.list();
      setVolunteers(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load volunteers');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchVolunteers();
    }
  }, [isAuthenticated]);

  const handleCreateVolunteer = async (data: VolunteerInput) => {
    await volunteersApi.create(data);
    await fetchVolunteers();
  };

  const handleUpdateVolunteer = async (data: VolunteerInput) => {
    if (editingVolunteer) {
      await volunteersApi.update(editingVolunteer.id, data);
      await fetchVolunteers();
      setEditingVolunteer(null);
    }
  };

  const handleDeleteVolunteer = async (volunteerId: string) => {
    if (confirm('Are you sure you want to delete this volunteer? This action cannot be undone.')) {
      try {
        await volunteersApi.delete(volunteerId);
        await fetchVolunteers();
      } catch (err: any) {
        alert(err.response?.data?.detail || err.message || 'Failed to delete volunteer');
      }
    }
  };

  const openCreateModal = () => {
    setEditingVolunteer(null);
    setIsModalOpen(true);
  };

  const openEditModal = (volunteer: Volunteer) => {
    setEditingVolunteer(volunteer);
    setIsModalOpen(true);
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

  // Calculate statistics
  const reliableCount = volunteers.filter((v) => v.no_show_rate < 0.2).length;
  const moderateCount = volunteers.filter((v) => v.no_show_rate >= 0.2 && v.no_show_rate < 0.4).length;
  const highRiskCount = volunteers.filter((v) => v.no_show_rate >= 0.4).length;

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Volunteers</h1>
            <p className="text-gray-600">Manage volunteer database and availability</p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={fetchVolunteers}
              className="px-4 py-2 bg-white text-blue-600 font-medium border border-blue-600 rounded-md hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Refresh
            </button>
            <button
              onClick={openCreateModal}
              className="px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center space-x-2"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span>Add Volunteer</span>
            </button>
          </div>
        </div>

        {loading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading volunteers...</p>
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
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
                <div>
                  <p className="text-3xl font-bold text-blue-600">{volunteers.length}</p>
                  <p className="text-sm text-gray-600">Total Volunteers</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-green-600">{reliableCount}</p>
                  <p className="text-sm text-gray-600">Reliable (&lt;20% no-show)</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-yellow-600">{moderateCount}</p>
                  <p className="text-sm text-gray-600">Moderate (20-40% no-show)</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-red-600">{highRiskCount}</p>
                  <p className="text-sm text-gray-600">High Risk (&gt;40% no-show)</p>
                </div>
              </div>
            </div>

            {volunteers.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg shadow">
                <svg className="h-16 w-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                <p className="text-gray-500 text-lg font-medium">No volunteers found</p>
                <p className="text-gray-400 text-sm mt-2">Add volunteers to get started</p>
                <button
                  onClick={openCreateModal}
                  className="mt-4 px-6 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700"
                >
                  Add Your First Volunteer
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {volunteers.map((volunteer) => (
                  <VolunteerCard
                    key={volunteer.id}
                    volunteer={volunteer}
                    onEdit={() => openEditModal(volunteer)}
                    onDelete={() => handleDeleteVolunteer(volunteer.id)}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </div>

      <VolunteerModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingVolunteer(null);
        }}
        onSubmit={editingVolunteer ? handleUpdateVolunteer : handleCreateVolunteer}
        volunteer={editingVolunteer}
      />
    </div>
  );
}
