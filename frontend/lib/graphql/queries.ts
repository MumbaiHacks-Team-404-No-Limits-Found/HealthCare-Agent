/**
 * GraphQL queries and mutations
 */
import { gql } from '@apollo/client';

// Fragments for reusable fields
export const CAMP_FIELDS = gql`
  fragment CampFields on CampType {
    id
    name
    location
    start
    end
    requirements {
      role
      count
      slot
    }
  }
`;

export const VOLUNTEER_FIELDS = gql`
  fragment VolunteerFields on VolunteerType {
    id
    name
    phone
    skills
    noShowRate
  }
`;

export const ASSIGNMENT_FIELDS = gql`
  fragment AssignmentFields on AssignmentType {
    id
    campId
    volunteerId
    role
    slot
    status
    isBackup
    createdAt
    volunteer {
      id
      name
      phone
      skills
      noShowRate
    }
  }
`;

// Queries
export const GET_CAMPS = gql`
  query GetCamps {
    camps {
      ...CampFields
    }
  }
  ${CAMP_FIELDS}
`;

export const GET_CAMP = gql`
  query GetCamp($id: String!) {
    camp(id: $id) {
      ...CampFields
    }
  }
  ${CAMP_FIELDS}
`;

export const GET_VOLUNTEERS = gql`
  query GetVolunteers {
    volunteers {
      ...VolunteerFields
    }
  }
  ${VOLUNTEER_FIELDS}
`;

export const GET_ASSIGNMENTS = gql`
  query GetAssignments($campId: String!) {
    assignments(campId: $campId) {
      ...AssignmentFields
    }
  }
  ${ASSIGNMENT_FIELDS}
`;

// Note: The assignments query requires a campId filter
// For showing all assignments, you may need to fetch all camps first
// or use a different approach

export const GET_CAMP_ACTIVITY = gql`
  query GetCampActivity($campId: String!) {
    campActivity(campId: $campId) {
      id
      campId
      timestamp
      event
      meta
    }
  }
`;

// Mutations
export const RUN_FORECAST = gql`
  mutation RunForecast($campId: String!) {
    runForecast(campId: $campId) {
      role
      slot
      mean
      upper90
      lower10
    }
  }
`;

export const RUN_PLAN = gql`
  mutation RunPlan($campId: String!) {
    runPlan(campId: $campId) {
      ...AssignmentFields
    }
  }
  ${ASSIGNMENT_FIELDS}
`;

export const REPLAN_CAMP = gql`
  mutation ReplanCamp($campId: String!) {
    replanCamp(campId: $campId) {
      ...AssignmentFields
    }
  }
  ${ASSIGNMENT_FIELDS}
`;

