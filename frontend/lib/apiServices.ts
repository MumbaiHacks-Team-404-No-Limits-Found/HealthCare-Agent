/**
 * REST API Services for CRUD operations
 * Maps directly to backend endpoints
 */
import api from './api';
import { Camp, CampInput, Volunteer, VolunteerInput, Assignment, AssignmentInput, ActivityLog } from './types';

// ============ CAMPS API ============

export const campsApi = {
  /**
   * GET /api/camps/ - List all camps
   */
  list: async (): Promise<Camp[]> => {
    const response = await api.get('/api/camps/');
    return response.data;
  },

  /**
   * POST /api/camps/ - Create a new camp
   */
  create: async (data: CampInput): Promise<Camp> => {
    const response = await api.post('/api/camps/', data);
    return response.data;
  },

  /**
   * GET /api/camps/{camp_id} - Get a specific camp
   */
  get: async (campId: string): Promise<Camp> => {
    const response = await api.get(`/api/camps/${campId}`);
    return response.data;
  },

  /**
   * PUT /api/camps/{camp_id} - Update a camp
   */
  update: async (campId: string, data: CampInput): Promise<Camp> => {
    const response = await api.put(`/api/camps/${campId}`, data);
    return response.data;
  },

  /**
   * DELETE /api/camps/{camp_id} - Delete a camp
   */
  delete: async (campId: string): Promise<void> => {
    await api.delete(`/api/camps/${campId}`);
  },
};

// ============ VOLUNTEERS API ============

export const volunteersApi = {
  /**
   * GET /api/volunteers/ - List all volunteers
   */
  list: async (): Promise<Volunteer[]> => {
    const response = await api.get('/api/volunteers/');
    return response.data;
  },

  /**
   * POST /api/volunteers/ - Create a new volunteer
   */
  create: async (data: VolunteerInput): Promise<Volunteer> => {
    const response = await api.post('/api/volunteers/', data);
    return response.data;
  },

  /**
   * GET /api/volunteers/{volunteer_id} - Get a specific volunteer
   */
  get: async (volunteerId: string): Promise<Volunteer> => {
    const response = await api.get(`/api/volunteers/${volunteerId}`);
    return response.data;
  },

  /**
   * PUT /api/volunteers/{volunteer_id} - Update a volunteer
   */
  update: async (volunteerId: string, data: VolunteerInput): Promise<Volunteer> => {
    const response = await api.put(`/api/volunteers/${volunteerId}`, data);
    return response.data;
  },

  /**
   * DELETE /api/volunteers/{volunteer_id} - Delete a volunteer
   */
  delete: async (volunteerId: string): Promise<void> => {
    await api.delete(`/api/volunteers/${volunteerId}`);
  },
};

// ============ ASSIGNMENTS API ============

export const assignmentsApi = {
  /**
   * GET /api/assignments/ - List all assignments (with optional filters)
   */
  list: async (params?: { camp_id?: string; volunteer_id?: string; status?: string }): Promise<Assignment[]> => {
    const response = await api.get('/api/assignments/', { params });
    return response.data;
  },

  /**
   * POST /api/assignments/ - Create a new assignment
   */
  create: async (data: AssignmentInput): Promise<Assignment> => {
    const response = await api.post('/api/assignments/', data);
    return response.data;
  },

  /**
   * GET /api/assignments/{assignment_id} - Get a specific assignment
   */
  get: async (assignmentId: string): Promise<Assignment> => {
    const response = await api.get(`/api/assignments/${assignmentId}`);
    return response.data;
  },

  /**
   * PATCH /api/assignments/{assignment_id} - Update assignment status
   */
  updateStatus: async (assignmentId: string, status: string): Promise<Assignment> => {
    const response = await api.patch(`/api/assignments/${assignmentId}`, { status });
    return response.data;
  },

  /**
   * DELETE /api/assignments/{assignment_id} - Delete an assignment
   */
  delete: async (assignmentId: string): Promise<void> => {
    await api.delete(`/api/assignments/${assignmentId}`);
  },
};

// ============ ACTIVITY LOGS API ============

export const activityApi = {
  /**
   * GET /api/activity/camp/{camp_id} - Get activity logs for a camp
   */
  getCampActivity: async (campId: string): Promise<ActivityLog[]> => {
    const response = await api.get(`/api/activity/camp/${campId}`);
    return response.data;
  },
};

// ============ NOTIFICATIONS API ============

export const notificationsApi = {
  /**
   * POST /notify/whatsapp - Send WhatsApp notification
   */
  sendWhatsApp: async (phone: string, message: string): Promise<any> => {
    const response = await api.post('/notify/whatsapp', { phone, message });
    return response.data;
  },
};

