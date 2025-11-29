/**
 * Modal component for creating/editing camps
 */
'use client';

import React, { useState, useEffect } from 'react';
import { Camp, CampInput, Requirement } from '@/lib/types';

interface CampModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CampInput) => Promise<void>;
  camp?: Camp | null;
  title?: string;
}

export default function CampModal({ isOpen, onClose, onSubmit, camp, title }: CampModalProps) {
  const [formData, setFormData] = useState<CampInput>({
    name: '',
    location: '',
    start: '',
    end: '',
    requirements: [],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // New requirement form
  const [newReq, setNewReq] = useState<Requirement>({
    role: '',
    count: 1,
    slot: '',
  });

  useEffect(() => {
    if (camp) {
      setFormData({
        name: camp.name,
        location: camp.location,
        start: camp.start,
        end: camp.end,
        requirements: camp.requirements || [],
      });
    } else {
      setFormData({
        name: '',
        location: '',
        start: '',
        end: '',
        requirements: [],
      });
    }
  }, [camp, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (formData.requirements.length === 0) {
        setError('Please add at least one requirement');
        setLoading(false);
        return;
      }
      await onSubmit(formData);
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to save camp');
    } finally {
      setLoading(false);
    }
  };

  const addRequirement = () => {
    if (!newReq.role || !newReq.slot || newReq.count < 1) {
      setError('Please fill all requirement fields');
      return;
    }
    setFormData({
      ...formData,
      requirements: [...formData.requirements, { ...newReq }],
    });
    setNewReq({ role: '', count: 1, slot: '' });
    setError('');
  };

  const removeRequirement = (index: number) => {
    setFormData({
      ...formData,
      requirements: formData.requirements.filter((_, i) => i !== index),
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75" onClick={onClose}></div>

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
          <form onSubmit={handleSubmit}>
            <div className="bg-white px-6 pt-6 pb-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-2xl font-bold text-gray-900">
                  {title || (camp ? 'Edit Camp' : 'Create New Camp')}
                </h3>
                <button
                  type="button"
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {error && (
                <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-3">
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              )}

              <div className="space-y-4">
                {/* Name */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Camp Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 placeholder-gray-400"
                    placeholder="e.g., Rural Health Camp 2024"
                  />
                </div>

                {/* Location */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Location *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 placeholder-gray-400"
                    placeholder="e.g., Village Community Center"
                  />
                </div>

                {/* Start and End Dates */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Start Date & Time *
                    </label>
                    <input
                      type="datetime-local"
                      required
                      value={formData.start}
                      onChange={(e) => setFormData({ ...formData, start: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      End Date & Time *
                    </label>
                    <input
                      type="datetime-local"
                      required
                      value={formData.end}
                      onChange={(e) => setFormData({ ...formData, end: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900"
                    />
                  </div>
                </div>

                {/* Requirements */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Requirements *
                  </label>
                  
                  {/* Existing requirements */}
                  {formData.requirements.length > 0 && (
                    <div className="mb-3 space-y-2">
                      {formData.requirements.map((req, index) => (
                        <div key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded-md">
                          <div className="flex-1">
                            <span className="font-medium text-gray-900">{req.count}x {req.role}</span>
                            <span className="text-gray-600"> - {req.slot}</span>
                          </div>
                          <button
                            type="button"
                            onClick={() => removeRequirement(index)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Add new requirement */}
                  <div className="border border-gray-300 rounded-md p-3">
                    <div className="grid grid-cols-12 gap-2">
                      <div className="col-span-4">
                        <input
                          type="text"
                          placeholder="Role (e.g., doctor)"
                          value={newReq.role}
                          onChange={(e) => setNewReq({ ...newReq, role: e.target.value })}
                          className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:ring-1 focus:ring-blue-500 text-gray-900 placeholder-gray-400"
                        />
                      </div>
                      <div className="col-span-2">
                        <input
                          type="number"
                          min="1"
                          placeholder="Count"
                          value={newReq.count}
                          onChange={(e) => setNewReq({ ...newReq, count: parseInt(e.target.value) || 1 })}
                          className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:ring-1 focus:ring-blue-500 text-gray-900 placeholder-gray-400"
                        />
                      </div>
                      <div className="col-span-4">
                        <input
                          type="text"
                          placeholder="Slot (e.g., morning)"
                          value={newReq.slot}
                          onChange={(e) => setNewReq({ ...newReq, slot: e.target.value })}
                          className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:ring-1 focus:ring-blue-500 text-gray-900 placeholder-gray-400"
                        />
                      </div>
                      <div className="col-span-2">
                        <button
                          type="button"
                          onClick={addRequirement}
                          className="w-full px-2 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                        >
                          Add
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="bg-gray-50 px-6 py-4 flex justify-end space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 font-medium"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium disabled:opacity-50"
              >
                {loading ? 'Saving...' : (camp ? 'Update Camp' : 'Create Camp')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

