/**
 * Custom hooks for GraphQL operations
 */
'use client';

import { useQuery, useMutation, QueryHookOptions, MutationHookOptions } from '@apollo/client';
import {
  GET_CAMPS,
  GET_CAMP,
  GET_VOLUNTEERS,
  GET_ASSIGNMENTS,
  GET_CAMP_ACTIVITY,
  RUN_FORECAST,
  RUN_PLAN,
  REPLAN_CAMP,
} from '@/lib/graphql/queries';

// Types
export interface Camp {
  id: string;
  name: string;
  location: string;
  start: string;
  end: string;
  requirements: {
    role: string;
    count: number;
    slot: string;
  }[];
}

export interface Volunteer {
  id: string;
  name: string;
  phone: string;
  skills: string[];
  noShowRate: number;
}

export interface Assignment {
  id: string;
  campId: string;
  volunteerId: string;
  role: string;
  slot: string;
  status: string;
  isBackup: boolean;
  createdAt: string;
  volunteer?: {
    id: string;
    name: string;
    phone: string;
    skills: string[];
  };
}

export interface ActivityLog {
  id: string;
  campId: string;
  timestamp: string;
  event: string;
  meta: string;
}

// Hooks
export function useCamps(options?: QueryHookOptions) {
  return useQuery<{ camps: Camp[] }>(GET_CAMPS, {
    ...options,
    fetchPolicy: options?.fetchPolicy || 'cache-and-network',
  });
}

export function useCamp(id: string, options?: QueryHookOptions) {
  return useQuery<{ camp: Camp }>(
    GET_CAMP,
    {
      variables: { id },
      skip: !id,
      ...options,
      fetchPolicy: options?.fetchPolicy || 'cache-and-network',
    }
  );
}

export function useVolunteers(options?: QueryHookOptions) {
  return useQuery<{ volunteers: Volunteer[] }>(GET_VOLUNTEERS, {
    ...options,
    fetchPolicy: options?.fetchPolicy || 'cache-and-network',
  });
}

export function useAssignments(campId: string, options?: QueryHookOptions) {
  return useQuery<{ assignments: Assignment[] }>(
    GET_ASSIGNMENTS,
    {
      variables: { campId },
      skip: !campId,
      ...options,
      fetchPolicy: options?.fetchPolicy || 'cache-and-network',
    }
  );
}

export function useCampActivity(campId: string, options?: QueryHookOptions) {
  return useQuery<{ campActivity: ActivityLog[] }>(
    GET_CAMP_ACTIVITY,
    {
      variables: { campId },
      skip: !campId,
      ...options,
      fetchPolicy: options?.fetchPolicy || 'cache-and-network',
    }
  );
}

export function useRunForecast(options?: MutationHookOptions) {
  return useMutation<{ runForecast: any[] }>(RUN_FORECAST, {
    ...options,
    refetchQueries: ['GetCamp'],
  });
}

export function useRunPlan(options?: MutationHookOptions) {
  return useMutation<{ runPlan: Assignment[] }>(RUN_PLAN, {
    ...options,
    refetchQueries: ['GetCamp', 'GetAssignments'],
  });
}

export function useReplanCamp(options?: MutationHookOptions) {
  return useMutation<{ replanCamp: Assignment[] }>(REPLAN_CAMP, {
    ...options,
    refetchQueries: ['GetCamp', 'GetAssignments'],
  });
}

