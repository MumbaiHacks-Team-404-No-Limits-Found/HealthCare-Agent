/**
 * Modal component for creating assignments
 */
'use client';

import React, { useState, useEffect } from 'react';
import { AssignmentInput, Camp, Volunteer } from '@/lib/types';

interface AssignmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: AssignmentInput) => Promise<void>;
  camps: Camp[];
  volunteers: Volunteer[];
  title?: string;
}

export default function AssignmentModal({ isOpen, onClose, onSubmit, camps, volunteers, title }: AssignmentModalProps) {
  const [formData, setFormData] = useState<AssignmentInput>({
    camp_id: '',
    volunteer_id: '',
    role: '',
    slot: '',
    status: 'assigned',
    is_backup: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedCamp, setSelectedCamp] = useState<Camp | null>(null);

  useEffect(() => {
    if (!isOpen) {
      setFormData({
        camp_id: '',
        volunteer_id: '',
        role: '',
        slot: '',
        status: 'assigned',
        is_backup: false,
      });
      setSelectedCamp(null);
      setError('');
    }
  }, [isOpen]);

  useEffect(() => {
    if (formData.camp_id) {
      const camp = camps.find((c) => c.id === formData.camp_id);
      setSelectedCamp(camp || null);
    }
  }, [formData.camp_id, camps]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await onSubmit(formData);
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to create assignment');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  // Get unique roles and slots from selected camp's requirements
  const availableRoles = selectedCamp 
    ? Array.from(new Set(selectedCamp.requirements.map((r) => r.role)))
    : [];
  const availableSlots = selectedCamp
    ? Array.from(new Set(selectedCamp.requirements.map((r) => r.slot)))
    : [];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75" onClick={onClose}></div>

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <form onSubmit={handleSubmit}>
            <div className="bg-white px-6 pt-6 pb-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-2xl font-bold text-gray-900">
                  {title || 'Create Assignment'}
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
                {/* Camp */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Camp *
                  </label>
                  <select
                    required
                    value={formData.camp_id}
                    onChange={(e) => setFormData({ ...formData, camp_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                  >
                    <option value="">Select a camp</option>
                    {camps.map((camp) => (
                      <option key={camp.id} value={camp.id}>
                        {camp.name} - {camp.location}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Volunteer */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Volunteer *
                  </label>
                  <select
                    required
                    value={formData.volunteer_id}
                    onChange={(e) => setFormData({ ...formData, volunteer_id: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                  >
                    <option value="">Select a volunteer</option>
                    {volunteers.map((volunteer) => (
                      <option key={volunteer.id} value={volunteer.id}>
                        {volunteer.name} - {volunteer.skills.join(', ')}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Role */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Role *
                  </label>
                  {availableRoles.length > 0 ? (
                    <select
                      required
                      value={formData.role}
                      onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                    >
                      <option value="">Select a role</option>
                      {availableRoles.map((role) => (
                        <option key={role} value={role}>
                          {role}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="text"
                      required
                      value={formData.role}
                      onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 placeholder-gray-400"
                      placeholder="e.g., doctor, nurse"
                    />
                  )}
                </div>

                {/* Slot */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Time Slot *
                  </label>
                  {availableSlots.length > 0 ? (
                    <select
                      required
                      value={formData.slot}
                      onChange={(e) => setFormData({ ...formData, slot: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                    >
                      <option value="">Select a slot</option>
                      {availableSlots.map((slot) => (
                        <option key={slot} value={slot}>
                          {slot}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="text"
                      required
                      value={formData.slot}
                      onChange={(e) => setFormData({ ...formData, slot: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 placeholder-gray-400"
                      placeholder="e.g., morning, afternoon"
                    />
                  )}
                </div>

                {/* Status */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Status
                  </label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                  >
                    <option value="assigned">Assigned</option>
                    <option value="confirmed">Confirmed</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>

                {/* Is Backup */}
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_backup"
                    checked={formData.is_backup}
                    onChange={(e) => setFormData({ ...formData, is_backup: e.target.checked })}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="is_backup" className="ml-2 block text-sm text-gray-700">
                    Mark as backup volunteer
                  </label>
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
                {loading ? 'Creating...' : 'Create Assignment'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

