/**
 * Modal component for creating/editing volunteers
 */
'use client';

import React, { useState, useEffect } from 'react';
import { Volunteer, VolunteerInput, AvailabilitySlot } from '@/lib/types';

interface VolunteerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: VolunteerInput) => Promise<void>;
  volunteer?: Volunteer | null;
  title?: string;
}

export default function VolunteerModal({ isOpen, onClose, onSubmit, volunteer, title }: VolunteerModalProps) {
  const [formData, setFormData] = useState<VolunteerInput>({
    name: '',
    phone: '',
    skills: [],
    availability: [],
    no_show_rate: 0.2,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [skillInput, setSkillInput] = useState('');

  // New availability slot
  const [newSlot, setNewSlot] = useState<AvailabilitySlot>({
    date: '',
    slots: [],
  });
  const [slotInput, setSlotInput] = useState('');

  useEffect(() => {
    if (volunteer) {
      setFormData({
        name: volunteer.name,
        phone: volunteer.phone,
        skills: volunteer.skills || [],
        availability: volunteer.availability || [],
        no_show_rate: volunteer.no_show_rate || 0.2,
      });
    } else {
      setFormData({
        name: '',
        phone: '',
        skills: [],
        availability: [],
        no_show_rate: 0.2,
      });
    }
  }, [volunteer, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (formData.skills.length === 0) {
        setError('Please add at least one skill');
        setLoading(false);
        return;
      }
      await onSubmit(formData);
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to save volunteer');
    } finally {
      setLoading(false);
    }
  };

  const addSkill = () => {
    if (!skillInput.trim()) return;
    if (formData.skills.includes(skillInput.trim())) {
      setError('Skill already added');
      return;
    }
    setFormData({
      ...formData,
      skills: [...formData.skills, skillInput.trim()],
    });
    setSkillInput('');
    setError('');
  };

  const removeSkill = (skill: string) => {
    setFormData({
      ...formData,
      skills: formData.skills.filter((s) => s !== skill),
    });
  };

  const addSlotToAvailability = () => {
    if (!slotInput.trim()) return;
    if (newSlot.slots.includes(slotInput.trim())) {
      setError('Slot already added');
      return;
    }
    setNewSlot({
      ...newSlot,
      slots: [...newSlot.slots, slotInput.trim()],
    });
    setSlotInput('');
    setError('');
  };

  const removeSlotFromAvailability = (slot: string) => {
    setNewSlot({
      ...newSlot,
      slots: newSlot.slots.filter((s) => s !== slot),
    });
  };

  const addAvailability = () => {
    if (!newSlot.date || newSlot.slots.length === 0) {
      setError('Please select a date and add at least one slot');
      return;
    }
    setFormData({
      ...formData,
      availability: [...formData.availability, { ...newSlot }],
    });
    setNewSlot({ date: '', slots: [] });
    setError('');
  };

  const removeAvailability = (index: number) => {
    setFormData({
      ...formData,
      availability: formData.availability.filter((_, i) => i !== index),
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
            <div className="bg-white px-6 pt-6 pb-4 max-h-[80vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-2xl font-bold text-gray-900">
                  {title || (volunteer ? 'Edit Volunteer' : 'Add New Volunteer')}
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
                    Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 placeholder-gray-400"
                    placeholder="e.g., Dr. John Smith"
                  />
                </div>

                {/* Phone */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Phone Number * (E.164 format)
                  </label>
                  <input
                    type="tel"
                    required
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 placeholder-gray-400"
                    placeholder="e.g., +919392664227"
                  />
                  <p className="text-xs text-gray-500 mt-1">Include country code (e.g., +91 for India)</p>
                </div>

                {/* Skills */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Skills/Roles *
                  </label>
                  
                  {/* Existing skills */}
                  {formData.skills.length > 0 && (
                    <div className="mb-3 flex flex-wrap gap-2">
                      {formData.skills.map((skill, index) => (
                        <span key={index} className="inline-flex items-center bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
                          {skill}
                          <button
                            type="button"
                            onClick={() => removeSkill(skill)}
                            className="ml-2 text-blue-600 hover:text-blue-800"
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Add new skill */}
                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="e.g., doctor, nurse, pharmacist"
                      value={skillInput}
                      onChange={(e) => setSkillInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addSkill())}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-gray-900 placeholder-gray-400"
                    />
                    <button
                      type="button"
                      onClick={addSkill}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                      Add
                    </button>
                  </div>
                </div>

                {/* No-Show Rate */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    No-Show Rate (0.0 - 1.0)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    value={formData.no_show_rate}
                    onChange={(e) => setFormData({ ...formData, no_show_rate: parseFloat(e.target.value) || 0.2 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-gray-900 placeholder-gray-400"
                  />
                  <p className="text-xs text-gray-500 mt-1">0.0 = always shows up, 1.0 = never shows up</p>
                </div>

                {/* Availability */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Availability (Optional)
                  </label>
                  
                  {/* Existing availability */}
                  {formData.availability.length > 0 && (
                    <div className="mb-3 space-y-2">
                      {formData.availability.map((avail, index) => (
                        <div key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded-md">
                          <div className="flex-1">
                            <span className="font-medium text-gray-900">{avail.date}</span>
                            <div className="text-sm text-gray-600 mt-1">
                              {avail.slots.join(', ')}
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={() => removeAvailability(index)}
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

                  {/* Add new availability */}
                  <div className="border border-gray-300 rounded-md p-3 space-y-2">
                    <input
                      type="date"
                      value={newSlot.date}
                      onChange={(e) => setNewSlot({ ...newSlot, date: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 text-gray-900"
                    />
                    
                    {newSlot.slots.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {newSlot.slots.map((slot, index) => (
                          <span key={index} className="inline-flex items-center bg-green-100 text-green-800 px-2 py-1 rounded text-xs">
                            {slot}
                            <button
                              type="button"
                              onClick={() => removeSlotFromAvailability(slot)}
                              className="ml-1 text-green-600 hover:text-green-800"
                            >
                              ×
                            </button>
                          </span>
                        ))}
                      </div>
                    )}
                    
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="e.g., morning, afternoon, evening"
                        value={slotInput}
                        onChange={(e) => setSlotInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addSlotToAvailability())}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 text-gray-900 placeholder-gray-400"
                      />
                      <button
                        type="button"
                        onClick={addSlotToAvailability}
                        className="px-3 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700"
                      >
                        Add Slot
                      </button>
                    </div>
                    
                    <button
                      type="button"
                      onClick={addAvailability}
                      disabled={!newSlot.date || newSlot.slots.length === 0}
                      className="w-full px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Add Availability
                    </button>
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
                {loading ? 'Saving...' : (volunteer ? 'Update Volunteer' : 'Add Volunteer')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

