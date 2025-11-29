'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import Navbar from '@/components/Navbar';
import CampCard from '@/components/CampCard';
import CampModal from '@/components/CampModal';
import { campsApi } from '@/lib/apiServices';
import { Camp, CampInput } from '@/lib/types';

export default function CampsPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [camps, setCamps] = useState<Camp[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCamp, setEditingCamp] = useState<Camp | null>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  const fetchCamps = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await campsApi.list();
      setCamps(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load camps');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchCamps();
    }
  }, [isAuthenticated]);

  const handleCreateCamp = async (data: CampInput) => {
    await campsApi.create(data);
    await fetchCamps();
  };

  const handleUpdateCamp = async (data: CampInput) => {
    if (editingCamp) {
      await campsApi.update(editingCamp.id, data);
      await fetchCamps();
      setEditingCamp(null);
    }
  };

  const handleDeleteCamp = async (campId: string) => {
    if (confirm('Are you sure you want to delete this camp? This action cannot be undone.')) {
      try {
        await campsApi.delete(campId);
        await fetchCamps();
      } catch (err: any) {
        alert(err.response?.data?.detail || err.message || 'Failed to delete camp');
      }
    }
  };

  const openCreateModal = () => {
    setEditingCamp(null);
    setIsModalOpen(true);
  };

  const openEditModal = (camp: Camp) => {
    setEditingCamp(camp);
    setIsModalOpen(true);
  };

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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Medical Camps</h1>
            <p className="text-gray-600">Manage all medical camp operations</p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={fetchCamps}
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
              <span>Create Camp</span>
            </button>
          </div>
        </div>

        {loading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading camps...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-600">{error}</p>
          </div>
        )}

        {!loading && !error && (
          <>
            {camps.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg shadow">
                <svg className="h-16 w-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
                <p className="text-gray-500 text-lg font-medium">No camps found</p>
                <p className="text-gray-400 text-sm mt-2">Create a new camp to get started</p>
                <button
                  onClick={openCreateModal}
                  className="mt-4 px-6 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700"
                >
                  Create Your First Camp
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {camps.map((camp) => (
                  <CampCard 
                    key={camp.id} 
                    camp={camp}
                    onEdit={() => openEditModal(camp)}
                    onDelete={() => handleDeleteCamp(camp.id)}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </div>

      <CampModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingCamp(null);
        }}
        onSubmit={editingCamp ? handleUpdateCamp : handleCreateCamp}
        camp={editingCamp}
      />
    </div>
  );
}

