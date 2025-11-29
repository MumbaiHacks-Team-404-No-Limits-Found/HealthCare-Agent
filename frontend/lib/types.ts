/**
 * Shared TypeScript types for the Healthcare Volunteer Coordinator app
 */

export interface Requirement {
  role: string;
  count: number;
  slot: string;
}

export interface Camp {
  id: string;
  name: string;
  location: string;
  start: string;
  end: string;
  requirements: Requirement[];
}

export interface AvailabilitySlot {
  date: string;
  slots: string[];
}

export interface Volunteer {
  id: string;
  name: string;
  phone: string;
  skills: string[];
  availability: AvailabilitySlot[];
  no_show_rate: number;
}

export interface Assignment {
  id: string;
  camp_id: string;
  volunteer_id: string;
  role: string;
  slot: string;
  status: string;
  is_backup: boolean;
}

export interface ActivityLog {
  timestamp: string;
  event: string;
  meta: Record<string, any>;
}

export interface User {
  id: string;
  email: string;
  role: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface CampInput {
  name: string;
  location: string;
  start: string;
  end: string;
  requirements: Requirement[];
}

export interface VolunteerInput {
  name: string;
  phone: string;
  skills: string[];
  availability: AvailabilitySlot[];
  no_show_rate: number;
}

export interface AssignmentInput {
  camp_id: string;
  volunteer_id: string;
  role: string;
  slot: string;
  status?: string;
  is_backup?: boolean;
}

