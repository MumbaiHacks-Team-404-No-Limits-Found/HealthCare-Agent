"""Strawberry GraphQL schema definitions."""
from typing import List, Optional, Dict
from datetime import datetime
import strawberry
from bson import ObjectId

from app.database import get_collection
from app.models import (
    Volunteer, VolunteerInput, Camp, CampInput, Assignment, 
    ForecastResult, ActivityLog, Requirement
)
from app.forecast import run_forecast_for_camp
from app.replan import get_camp_by_id, get_existing_assignments
from app.activity import log_activity, get_camp_activity
from app.utils import validate_object_id, get_camp_or_raise, get_assignment_or_raise


@strawberry.type
class VolunteerType:
    """GraphQL Volunteer type."""
    id: str
    name: str
    phone: str
    skills: List[str]
    no_show_rate: float


@strawberry.type
class RequirementType:
    """GraphQL Requirement type."""
    role: str
    count: int
    slot: str


@strawberry.type
class CampType:
    """GraphQL Camp type."""
    id: str
    name: str
    location: str
    start: str
    end: str
    requirements: List[RequirementType]


@strawberry.type
class AssignmentType:
    """GraphQL Assignment type."""
    id: str
    camp_id: str
    volunteer_id: str
    role: str
    slot: str
    status: str
    is_backup: bool
    created_at: str
    volunteer: Optional[VolunteerType] = None


@strawberry.type
class ForecastResultType:
    """GraphQL ForecastResult type."""
    role: str
    slot: str
    mean: float
    upper90: int
    lower10: int


@strawberry.type
class ActivityLogType:
    """GraphQL ActivityLog type."""
    id: str
    camp_id: str
    timestamp: str
    event: str
    meta: str  # JSON string for now


@strawberry.type
class WhatsAppMessageResponse:
    """GraphQL WhatsApp message response type."""
    sid: str
    status: str
    to: str
    timestamp: str
    delivered: bool


@strawberry.input
class AvailabilitySlotInput:
    """Input for availability slot."""
    date: str
    slots: List[str]


@strawberry.input
class VolunteerInputType:
    """Input for creating a volunteer."""
    name: str
    phone: str
    skills: List[str] = strawberry.field(default_factory=list)
    availability: List[AvailabilitySlotInput] = strawberry.field(default_factory=list)
    no_show_rate: float = 0.2


@strawberry.input
class RequirementInput:
    """Input for requirement."""
    role: str
    count: int
    slot: str


@strawberry.input
class CampInputType:
    """Input for creating a camp."""
    name: str
    location: str
    start: str
    end: str
    requirements: List[RequirementInput] = strawberry.field(default_factory=list)


@strawberry.type
class Query:
    """GraphQL queries."""
    
    @strawberry.field
    async def camps(self) -> List[CampType]:
        """
        Get all camps.
        
        MongoDB Collections:
            - camps: Reads all documents from collection
        
        Returns:
            List[CampType] with fields:
            - id: String! (ObjectId as string)
            - name: String!
            - location: String!
            - start: String! (ISO datetime string)
            - end: String! (ISO datetime string)
            - requirements: [CampRequirement!]! (embedded array)
                * role: String!
                * count: Int!
                * slot: String (optional)
        """
        try:
            collection = get_collection("camps")
            cursor = collection.find({})
            camps = []
            async for doc in cursor:
                try:
                    camp = Camp(**doc)
                    camps.append(CampType(
                        id=str(camp.id),
                        name=camp.name,
                        location=camp.location,
                        start=camp.start,
                        end=camp.end,
                        requirements=[
                            RequirementType(role=r.role, count=r.count, slot=r.slot)
                            for r in camp.requirements
                        ]
                    ))
                except Exception as e:
                    # Skip invalid documents, log error
                    print(f"Warning: Skipping invalid camp document: {e}")
                    continue
            return camps
        except Exception as e:
            raise ValueError(f"Error fetching camps: {str(e)}")
    
    @strawberry.field
    async def camp(self, id: str) -> Optional[CampType]:
        """
        Get a camp by ID.
        
        MongoDB Collections:
            - camps: Queries by _id (ObjectId)
        
        Args:
            id: String! (Camp ID, must be valid ObjectId format)
                Validated using utils.validate_object_id()
            
        Returns:
            CampType if found, None if not found or invalid ID
            Same structure as camps query
        """
        try:
            # Validate ObjectId format
            validate_object_id(id, "Camp")
            camp = await get_camp_by_id(id)
            return CampType(
                id=str(camp.id),
                name=camp.name,
                location=camp.location,
                start=camp.start,
                end=camp.end,
                requirements=[
                    RequirementType(role=r.role, count=r.count, slot=r.slot)
                    for r in camp.requirements
                ]
            )
        except ValueError:
            # Return None for invalid ID or not found (GraphQL convention)
            return None
        except Exception as e:
            raise ValueError(f"Error fetching camp: {str(e)}")
    
    @strawberry.field
    async def volunteers(self) -> List[VolunteerType]:
        """
        Get all volunteers.
        
        MongoDB Collections:
            - volunteers: Reads all documents from collection
        
        Returns:
            List[VolunteerType] with fields:
            - id: String! (ObjectId as string)
            - name: String!
            - phone: String!
            - skills: [String!]! (array of skill strings)
            - availability: [VolunteerAvailability!] (optional, if present in DB)
            - noShowRate: Float (camelCase, maps from no_show_rate in DB)
        """
        try:
            collection = get_collection("volunteers")
            cursor = collection.find({})
            volunteers = []
            async for doc in cursor:
                try:
                    volunteer = Volunteer(**doc)
                    volunteers.append(VolunteerType(
                        id=str(volunteer.id),
                        name=volunteer.name,
                        phone=volunteer.phone,
                        skills=volunteer.skills,
                        no_show_rate=volunteer.no_show_rate
                    ))
                except Exception as e:
                    # Skip invalid documents, log error
                    print(f"Warning: Skipping invalid volunteer document: {e}")
                    continue
            return volunteers
        except Exception as e:
            raise ValueError(f"Error fetching volunteers: {str(e)}")
    
    @strawberry.field
    async def assignments(self, camp_id: str) -> List[AssignmentType]:
        """
        Get assignments for a camp.
        
        MongoDB Collections:
            - assignments: Queries by camp_id (ObjectId)
            - volunteers: Fetches volunteer details for nested volunteer field
        
        Args:
            camp_id: String! (Camp ID, must be valid ObjectId format)
                Validated using utils.validate_object_id()
            
        Returns:
            List[AssignmentType] with fields:
            - id: String! (ObjectId as string)
            - campId: String! (camelCase, maps from camp_id)
            - volunteerId: String! (camelCase, maps from volunteer_id)
            - role: String!
            - slot: String (optional)
            - status: String! (e.g., "assigned", "confirmed", "cancelled", "backup")
            - isBackup: Boolean! (camelCase, maps from is_backup)
            - volunteer: Volunteer (optional nested field with volunteer details)
        """
        try:
            # Validate ObjectId format
            validate_object_id(camp_id, "Camp")
            
            collection = get_collection("assignments")
            cursor = collection.find({"camp_id": ObjectId(camp_id)})
            assignments = []
            async for doc in cursor:
                try:
                    assignment = Assignment(**doc)
                    assignments.append(AssignmentType(
                        id=str(assignment.id),
                        camp_id=str(assignment.camp_id),
                        volunteer_id=str(assignment.volunteer_id),
                        role=assignment.role,
                        slot=assignment.slot,
                        status=assignment.status,
                        is_backup=assignment.is_backup,
                        created_at=assignment.created_at.isoformat()
                    ))
                except Exception as e:
                    # Skip invalid documents, log error
                    print(f"Warning: Skipping invalid assignment document: {e}")
                    continue
            return assignments
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise ValueError(f"Error fetching assignments: {str(e)}")
    
    @strawberry.field
    async def camp_activity(self, camp_id: str) -> List[ActivityLogType]:
        """
        Get activity logs for a camp.
        
        MongoDB Collections:
            - activity_logs: Queries by camp_id (ObjectId), sorted by timestamp descending
        
        Args:
            camp_id: String! (Camp ID, must be valid ObjectId format)
                Validated using utils.validate_object_id()
            
        Returns:
            List[ActivityLogType] with fields:
            - id: String! (ObjectId as string)
            - campId: String! (camelCase, maps from camp_id)
            - event: String! (event description)
            - metadata: JSON / dict (additional metadata, currently returned as string)
            - timestamp: String! (ISO datetime string)
        """
        try:
            # Validate ObjectId format
            validate_object_id(camp_id, "Camp")
            
            logs = await get_camp_activity(camp_id)
            return [
                ActivityLogType(
                    id=str(log.id),
                    camp_id=str(log.camp_id),
                    timestamp=log.timestamp.isoformat(),
                    event=log.event,
                    meta=str(log.meta)  # Simple string representation
                )
                for log in logs
            ]
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise ValueError(f"Error fetching camp activity: {str(e)}")


@strawberry.type
class Mutation:
    """GraphQL mutations."""
    
    @strawberry.mutation
    async def create_volunteer(self, input: VolunteerInputType) -> VolunteerType:
        """
        Create a new volunteer.
        
        MongoDB Collections:
            - volunteers: Inserts new document
        
        Input Validation:
            - name: Required, non-empty string
            - phone: Required, non-empty string
            - skills: Optional array of strings (defaults to empty list)
            - availability: Optional array of AvailabilitySlotInput (defaults to empty list)
            - noShowRate: Optional float, must be in [0, 1] (defaults to 0.2)
        
        Args:
            input: VolunteerInputType with:
                - name: String!
                - phone: String!
                - skills: [String!]! (default: [])
                - availability: [VolunteerAvailabilityInput!] (optional)
                - noShowRate: Float (optional, default: 0.2, must be in [0,1])
            
        Returns:
            VolunteerType with created volunteer data (same structure as volunteers query)
            
        Raises:
            ValueError: If validation fails (empty name/phone, invalid noShowRate) or DB operation fails
        """
        try:
            # Validate required fields
            if not input.name or not input.name.strip():
                raise ValueError("Volunteer name is required")
            if not input.phone or not input.phone.strip():
                raise ValueError("Volunteer phone is required")
            
            # Validate no_show_rate is between 0 and 1
            if input.no_show_rate < 0 or input.no_show_rate > 1:
                raise ValueError("no_show_rate must be between 0 and 1")
            
            collection = get_collection("volunteers")
            
            volunteer_data = {
                "name": input.name.strip(),
                "phone": input.phone.strip(),
                "skills": input.skills or [],
                "availability": [
                    {"date": a.date, "slots": a.slots}
                    for a in (input.availability or [])
                ],
                "no_show_rate": input.no_show_rate
            }
            
            result = await collection.insert_one(volunteer_data)
            volunteer_data["_id"] = result.inserted_id
            
            volunteer = Volunteer(**volunteer_data)
            return VolunteerType(
                id=str(volunteer.id),
                name=volunteer.name,
                phone=volunteer.phone,
                skills=volunteer.skills,
                no_show_rate=volunteer.no_show_rate
            )
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise ValueError(f"Error creating volunteer: {str(e)}")
    
    @strawberry.mutation
    async def create_camp(self, input: CampInputType) -> CampType:
        """
        Create a new camp.
        
        MongoDB Collections:
            - camps: Inserts new document with embedded requirements array
            - activity_logs: Logs "camp_created" event (non-blocking)
        
        Side Effects:
            - Logs activity: "camp_created" with metadata {name: camp.name}
            - Schedules automated forecast and planning via Celery (non-blocking)
        
        Input Validation:
            - name: Required, non-empty string
            - location: Required, non-empty string
            - start: Required, non-empty ISO datetime string
            - end: Required, non-empty ISO datetime string
            - requirements: Optional array, each requirement must have:
                * role: Non-empty string
                * count: Non-negative integer
                * slot: Non-empty string
        
        Args:
            input: CampInputType with:
                - name: String!
                - location: String!
                - start: String! (ISO datetime)
                - end: String! (ISO datetime)
                - requirements: [CampRequirementInput!]! (array of role, count, slot)
            
        Returns:
            CampType with created camp data (same structure as camps query)
            
        Raises:
            ValueError: If validation fails or DB operation fails
        """
        try:
            # Validate required fields
            if not input.name or not input.name.strip():
                raise ValueError("Camp name is required")
            if not input.location or not input.location.strip():
                raise ValueError("Camp location is required")
            if not input.start or not input.start.strip():
                raise ValueError("Camp start time is required")
            if not input.end or not input.end.strip():
                raise ValueError("Camp end time is required")
            
            # Validate requirements
            if input.requirements:
                for req in input.requirements:
                    if not req.role or not req.role.strip():
                        raise ValueError("Requirement role cannot be empty")
                    if req.count < 0:
                        raise ValueError("Requirement count must be non-negative")
                    if not req.slot or not req.slot.strip():
                        raise ValueError("Requirement slot cannot be empty")
            
            collection = get_collection("camps")
            
            camp_data = {
                "name": input.name.strip(),
                "location": input.location.strip(),
                "start": input.start.strip(),
                "end": input.end.strip(),
                "requirements": [
                    {"role": r.role.strip(), "count": r.count, "slot": r.slot.strip()}
                    for r in (input.requirements or [])
                ]
            }
            
            result = await collection.insert_one(camp_data)
            camp_data["_id"] = result.inserted_id
            
            camp = Camp(**camp_data)
            
            # Log activity
            try:
                await log_activity(
                    str(camp.id),
                    "camp_created",
                    {"name": camp.name}
                )
            except Exception as e:
                # Log error but don't fail the mutation
                print(f"Warning: Failed to log camp creation activity: {e}")
            
            # Schedule automated forecast and planning via Celery
            try:
                from app.tasks.scheduler_tasks import schedule_camp_forecast_and_plan
                schedule_result = schedule_camp_forecast_and_plan.delay(str(camp.id))
                print(f"Scheduled forecast and planning for camp {camp.id} (task_id: {schedule_result.id})")
            except Exception as e:
                # Log error but don't fail the mutation
                print(f"Warning: Failed to schedule forecast/planning: {e}")
            
            return CampType(
                id=str(camp.id),
                name=camp.name,
                location=camp.location,
                start=camp.start,
                end=camp.end,
                requirements=[
                    RequirementType(role=r.role, count=r.count, slot=r.slot)
                    for r in camp.requirements
                ]
            )
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise ValueError(f"Error creating camp: {str(e)}")
    
    @strawberry.mutation
    async def run_forecast(self, camp_id: str) -> List[ForecastResultType]:
        """
        Run forecast for a camp using Poisson distribution.
        
        MongoDB Collections:
            - camps: Fetches camp by ID
            - role_demand_history: PRIMARY data source - queries by role and slot for historical demand counts
            - activity_logs: Logs "Forecast run for camp {name}" with metadata (non-blocking)
        
        Forecasting Logic (forecast.py):
            For each requirement:
            1. Attempts to fetch real historical counts from role_demand_history collection
               - Queries by role (required) and slot (optional)
            2. If real data available:
               - Computes lambda (mean) from historical counts: lambda = mean(historical_counts)
               - Clamps lambda to minimum 0.1 to avoid degenerate distributions
            3. If no real data (fallback):
               - Uses simulated historical counts (deterministic pattern based on requirement.count)
               - Computes lambda from simulated counts
            4. Calculates Poisson percentiles using scipy.stats.poisson:
               - mean = lambda
               - upper90 = poisson.ppf(0.9, lambda) (90th percentile)
               - lower10 = poisson.ppf(0.1, lambda) (10th percentile)
            5. Ensures non-negative results
        
        Args:
            camp_id: String! (Camp ID, must be valid ObjectId format)
                Validated using utils.validate_object_id()
            
        Returns:
            List[ForecastResultType] with fields:
            - role: String!
            - slot: String (optional)
            - mean: Float! (lambda parameter, mean of Poisson distribution)
            - upper90: Int! (90th percentile, upper bound)
            - lower10: Int! (10th percentile, lower bound)
            
        Raises:
            ValueError: If camp_id is invalid, camp not found, or camp has no requirements
        """
        try:
            # Validate and fetch camp
            camp = await get_camp_or_raise(camp_id)
            
            # Validate camp has requirements
            if not camp.requirements:
                raise ValueError(f"Camp {camp_id} has no requirements to forecast")
            
            # Run forecast
            results = await run_forecast_for_camp(camp)
            
            # Log activity (non-blocking)
            try:
                await log_activity(
                    camp_id,
                    f"Forecast run for camp {camp.name}",
                    {
                        "requirements_count": len(camp.requirements),
                        "camp_name": camp.name
                    }
                )
            except Exception as e:
                print(f"Warning: Failed to log forecast activity: {e}")
            
            # Return forecast results
            return [
                ForecastResultType(
                    role=r.role,
                    slot=r.slot,
                    mean=r.mean,
                    upper90=int(r.upper_90),
                    lower10=int(r.lower_10)
                )
                for r in results
            ]
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise ValueError(f"Error running forecast: {str(e)}")
    
    @strawberry.mutation
    async def run_plan(self, camp_id: str) -> List[AssignmentType]:
        """
        Run planning for a camp using OR-Tools ILP solver.
        
        MongoDB Collections:
            - camps: Fetches camp by ID
            - volunteers: Fetches all volunteers for eligibility checking
            - assignments: Fetches existing assignments for this camp
            - assignments: Inserts new assignments with status="assigned"
            - activity_logs: Logs "Plan run for camp {name}" with metadata (non-blocking)
        
        Planning Logic (planner.py):
            Uses OR-Tools Integer Linear Programming (ILP) with greedy fallback:
            
            1. Eligibility Check (is_volunteer_eligible_for_requirement):
               - Volunteer must have required skill (role in volunteer.skills)
               - Volunteer must be available for slot (slot in volunteer.availability)
               - Excludes volunteers already confirmed for this camp
            
            2. OR-Tools ILP Solver:
               - Variables: x[v_idx, r_idx] in {0,1} for eligible (volunteer, requirement) pairs
               - Constraints:
                 * For each requirement i: Σ_v x[v,i] + confirmed_count_i >= requirement.count
                 * For each volunteer v: Σ_i x[v,i] <= 1 (each volunteer assigned to at most one requirement)
               - Objective: Maximize Σ_v Σ_i x[v,i] (maximize filled slots)
               - Time limit: 3000ms (3 seconds)
            
            3. Fallback (if ILP fails):
               - Greedy algorithm: Processes requirements in order, assigns eligible volunteers
               - Tries to fill as much demand as possible
            
            4. Preserves confirmed assignments (never disturbs them)
            
            5. Computes unfilled_slots = total_required - (confirmed + newly_assigned)
        
        Side Effects:
            - Persists new assignments to MongoDB with status="assigned" and is_backup=False
            - Logs activity with metadata: {assignments_created, requirements_count, unfilled_slots}
            - Schedules batch notifications via Celery (non-blocking)
        
        Args:
            camp_id: String! (Camp ID, must be valid ObjectId format)
                Validated using utils.validate_object_id()
            
        Returns:
            List[AssignmentType] with newly created assignments (same structure as assignments query)
            Includes nested volunteer field with volunteer details
            
        Raises:
            ValueError: If camp_id is invalid, camp not found, or camp has no requirements
        """
        try:
            # Validate and fetch camp
            camp = await get_camp_or_raise(camp_id)
            
            # Validate camp has requirements
            if not camp.requirements:
                raise ValueError(f"Camp {camp_id} has no requirements to plan")
            
            # Validate ObjectId format for planner
            camp_object_id = validate_object_id(camp_id, "Camp")
            
            # Run planner (this persists assignments)
            from app.planner import run_planner_for_camp
            created_assignments, unfilled_slots = await run_planner_for_camp(camp_object_id)
            
            # Fetch volunteers for the created assignments
            volunteers_collection = get_collection("volunteers")
            volunteer_map: Dict[str, Volunteer] = {}
            
            if created_assignments:
                volunteer_ids = [assign.volunteer_id for assign in created_assignments]
                cursor = volunteers_collection.find({"_id": {"$in": volunteer_ids}})
                async for doc in cursor:
                    try:
                        volunteer = Volunteer(**doc)
                        volunteer_map[str(volunteer.id)] = volunteer
                    except Exception as e:
                        print(f"Warning: Skipping invalid volunteer document: {e}")
                        continue
            
            # Build assignment types with nested volunteer info
            assignment_types = []
            for assignment in created_assignments:
                volunteer_id_str = str(assignment.volunteer_id)
                volunteer = volunteer_map.get(volunteer_id_str)
                
                volunteer_type = None
                if volunteer:
                    volunteer_type = VolunteerType(
                        id=str(volunteer.id),
                        name=volunteer.name,
                        phone=volunteer.phone,
                        skills=volunteer.skills,
                        no_show_rate=volunteer.no_show_rate
                    )
                
                assignment_types.append(AssignmentType(
                    id=str(assignment.id),
                    camp_id=str(assignment.camp_id),
                    volunteer_id=volunteer_id_str,
                    role=assignment.role,
                    slot=assignment.slot,
                    status=assignment.status,
                    is_backup=assignment.is_backup,
                    created_at=assignment.created_at.isoformat(),
                    volunteer=volunteer_type
                ))
            
            # Log activity (non-blocking)
            try:
                await log_activity(
                    camp_id,
                    f"Plan run for camp {camp.name}",
                    {
                        "assignments_created": len(created_assignments),
                        "requirements_count": len(camp.requirements),
                        "unfilled_slots": unfilled_slots
                    }
                )
            except Exception as e:
                print(f"Warning: Failed to log plan activity: {e}")
            
            # Send notifications for new assignments via Celery
            if created_assignments:
                try:
                    from app.tasks.notification_tasks import send_batch_notifications
                    assignment_ids = [str(assign.id) for assign in created_assignments]
                    notification_result = send_batch_notifications.delay(assignment_ids)
                    print(f"Scheduled notifications for {len(assignment_ids)} assignments (task_id: {notification_result.id})")
                except Exception as e:
                    print(f"Warning: Failed to schedule notifications: {e}")
            
            return assignment_types
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise ValueError(f"Error running plan: {str(e)}")
    
    @strawberry.mutation
    async def mark_assignment_status(
        self,
        assignment_id: str,
        status: str
    ) -> Optional[AssignmentType]:
        """
        Mark assignment status (assigned, confirmed, cancelled, backup).
        
        MongoDB Collections:
            - assignments: Updates assignment document with new status
            - volunteers: Fetches volunteer details for nested volunteer field
            - activity_logs: Logs "assignment_status_changed" with metadata (non-blocking)
        
        Status Validation:
            - Must be one of: "assigned", "confirmed", "cancelled", "backup"
            - Raises ValueError if invalid status provided
        
        Side Effects:
            - Updates assignment status in MongoDB
            - Logs activity with metadata:
                * assignment_id: Updated assignment ID
                * status: New status
                * replan_suggested: true if status="cancelled"
            - Note: Does NOT automatically trigger replanning (frontend should call replanCamp)
        
        Args:
            assignment_id: String! (Assignment ID, must be valid ObjectId format)
                Validated using utils.validate_object_id()
            status: String! (New status, must be one of: "assigned", "confirmed", "cancelled", "backup")
            
        Returns:
            AssignmentType with updated assignment (same structure as assignments query)
            Includes nested volunteer field with volunteer details
            Returns None if assignment not found (should not happen after validation)
            
        Raises:
            ValueError: If assignment_id is invalid format, assignment not found, or status is invalid
        """
        try:
            # Validate status
            valid_statuses = {"assigned", "confirmed", "cancelled", "backup"}
            if status not in valid_statuses:
                raise ValueError(f"Invalid status: {status}. Must be one of: {', '.join(valid_statuses)}")
            
            # Validate and fetch assignment
            assignment = await get_assignment_or_raise(assignment_id)
            
            # Update status
            collection = get_collection("assignments")
            await collection.update_one(
                {"_id": assignment.id},
                {"$set": {"status": status}}
            )
            
            # Fetch updated assignment
            updated_doc = await collection.find_one({"_id": assignment.id})
            if not updated_doc:
                raise ValueError(f"Assignment {assignment_id} not found after update")
            
            assignment = Assignment(**updated_doc)
            
            # Log activity (non-blocking)
            try:
                await log_activity(
                    str(assignment.camp_id),
                    "assignment_status_changed",
                    {
                        "assignment_id": assignment_id,
                        "status": status,
                        "replan_suggested": status == "cancelled"
                    }
                )
            except Exception as e:
                print(f"Warning: Failed to log assignment status change: {e}")
            
            # Fetch volunteer info for the response
            volunteers_collection = get_collection("volunteers")
            volunteer_doc = await volunteers_collection.find_one({"_id": assignment.volunteer_id})
            volunteer_type = None
            
            if volunteer_doc:
                try:
                    volunteer = Volunteer(**volunteer_doc)
                    volunteer_type = VolunteerType(
                        id=str(volunteer.id),
                        name=volunteer.name,
                        phone=volunteer.phone,
                        skills=volunteer.skills,
                        no_show_rate=volunteer.no_show_rate
                    )
                except Exception as e:
                    print(f"Warning: Failed to load volunteer info: {e}")
            
            return AssignmentType(
                id=str(assignment.id),
                camp_id=str(assignment.camp_id),
                volunteer_id=str(assignment.volunteer_id),
                role=assignment.role,
                slot=assignment.slot,
                status=assignment.status,
                is_backup=assignment.is_backup,
                created_at=assignment.created_at.isoformat(),
                volunteer=volunteer_type
            )
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise ValueError(f"Error updating assignment status: {str(e)}")
    
    @strawberry.mutation
    async def replanCamp(self, camp_id: str) -> List[AssignmentType]:
        """
        Replan assignments for a camp.
        
        MongoDB Collections:
            - camps: Fetches camp by ID
            - assignments: Fetches existing assignments for this camp
            - assignments: Deletes all active (non-confirmed) assignments
            - assignments: Inserts new assignments with status="assigned"
            - volunteers: Fetches all volunteers for eligibility checking
            - activity_logs: Logs "Replan run for camp {name}" with metadata (non-blocking)
        
        Replanning Logic (replan.py):
            1. Classifies existing assignments:
               - confirmed_assignments: status == "confirmed" (PRESERVED, never changed)
               - cancelled_assignments: status == "cancelled"
               - active_assignments: status in ["assigned", "backup"] (DELETED)
            
            2. Computes remaining demand per requirement:
               - remaining = requirement.count - confirmed_count_for_that_role/slot
            
            3. Excludes from eligibility:
               - Cancelled volunteers for this camp (they cancelled, don't reassign)
               - Already confirmed volunteers (they stay in their current role/slot)
            
            4. Deletes all active (non-confirmed) assignments for this camp
            
            5. Calls planner (plan_assignments) with:
               - Confirmed assignments preserved as existing
               - Eligible volunteers (excludes cancelled and confirmed)
               - Planner fills remaining gaps using OR-Tools ILP (with greedy fallback)
            
            6. Inserts newly created assignments with status="assigned" and is_backup=False
            
            7. Computes still_unfilled_slots = total_required - (confirmed + newly_assigned)
        
        Side Effects:
            - Deletes old non-confirmed assignments
            - Persists new assignments to MongoDB
            - Logs activity with metadata: {new_assignments, still_unfilled_slots}
        
        Args:
            camp_id: String! (Camp ID, must be valid ObjectId format)
                Validated using utils.validate_object_id()
            
        Returns:
            List[AssignmentType] with ONLY NEW assignments created (confirmed ones are NOT returned)
            Same structure as assignments query, includes nested volunteer field
            
        Raises:
            ValueError: If camp_id is invalid, camp not found, or camp has no requirements
        """
        try:
            # Validate and fetch camp
            camp = await get_camp_or_raise(camp_id)
            
            # Validate camp has requirements
            if not camp.requirements:
                raise ValueError(f"Camp {camp_id} has no requirements to replan")
            
            # Validate ObjectId format for replan
            camp_object_id = validate_object_id(camp_id, "Camp")
            
            # Run replan (this persists new assignments)
            from app.replan import replan_camp as replan_camp_func
            new_assignments, unfilled_slots = await replan_camp_func(camp_object_id)
            
            # Fetch volunteers for the new assignments
            volunteers_collection = get_collection("volunteers")
            volunteer_map: Dict[str, Volunteer] = {}
            
            if new_assignments:
                volunteer_ids = [assign.volunteer_id for assign in new_assignments]
                cursor = volunteers_collection.find({"_id": {"$in": volunteer_ids}})
                async for doc in cursor:
                    try:
                        volunteer = Volunteer(**doc)
                        volunteer_map[str(volunteer.id)] = volunteer
                    except Exception as e:
                        print(f"Warning: Skipping invalid volunteer document: {e}")
                        continue
            
            # Build assignment types with nested volunteer info
            assignment_types = []
            for assignment in new_assignments:
                volunteer_id_str = str(assignment.volunteer_id)
                volunteer = volunteer_map.get(volunteer_id_str)
                
                volunteer_type = None
                if volunteer:
                    volunteer_type = VolunteerType(
                        id=str(volunteer.id),
                        name=volunteer.name,
                        phone=volunteer.phone,
                        skills=volunteer.skills,
                        no_show_rate=volunteer.no_show_rate
                    )
                
                assignment_types.append(AssignmentType(
                    id=str(assignment.id),
                    camp_id=str(assignment.camp_id),
                    volunteer_id=volunteer_id_str,
                    role=assignment.role,
                    slot=assignment.slot,
                    status=assignment.status,
                    is_backup=assignment.is_backup,
                    created_at=assignment.created_at.isoformat(),
                    volunteer=volunteer_type
                ))
            
            # Log activity (non-blocking)
            try:
                await log_activity(
                    camp_id,
                    f"Replan run for camp {camp.name}",
                    {
                        "new_assignments": len(new_assignments),
                        "still_unfilled_slots": unfilled_slots
                    }
                )
            except Exception as e:
                print(f"Warning: Failed to log replan activity: {e}")
            
            return assignment_types
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise ValueError(f"Error replanning camp: {str(e)}")
    
    @strawberry.mutation
    async def run_agent_workflow(
        self,
        camp_id: str,
        notify_volunteers: bool = True
    ) -> str:
        """
        Run the complete AI Agent workflow for a camp.
        
        Workflow Steps:
        1. Run forecast (Poisson distribution)
        2. Run planning (OR-Tools ILP)
        3. Notify volunteers via WhatsApp (if requested)
        4. Log all activities
        
        MongoDB Collections:
            - camps: Fetches camp by ID
            - role_demand_history: Used for forecasting
            - volunteers: Used for planning
            - assignments: Creates new assignments
            - activity_logs: Logs all workflow steps
        
        Side Effects:
            - Runs forecast and stores results
            - Creates assignments in MongoDB
            - Sends WhatsApp notifications (if requested)
            - Logs all activities
        
        Args:
            camp_id: String! (Camp ID, must be valid ObjectId format)
            notify_volunteers: Boolean (default: true) - Whether to send notifications
            
        Returns:
            String with workflow result summary (JSON format)
            
        Raises:
            ValueError: If camp_id is invalid or camp not found
        """
        try:
            from app.agent import MedicalCampAgent
            
            # Validate camp exists
            camp = await get_camp_or_raise(camp_id)
            
            # Run agent workflow
            agent = MedicalCampAgent()
            result = await agent.run_full_workflow(
                camp_id,
                notify_volunteers=notify_volunteers,
                use_celery=False  # Run synchronously for GraphQL
            )
            
            import json
            return json.dumps(result.to_dict())
            
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise ValueError(f"Agent workflow failed: {str(e)}")
    
    @strawberry.mutation(name="sendWhatsApp")
    async def send_whats_app(self, to: str, message: str) -> WhatsAppMessageResponse:
        """
        Send outbound WhatsApp message via Twilio REST API.
        
        External Services:
            - Twilio REST API: Sends WhatsApp message via client.messages.create()
        
        Implementation:
            Uses the same notifications.send_whatsapp_message() helper as /notify/whatsapp endpoint.
            Auto-formats phone number with "whatsapp:" prefix using format_whatsapp_number().
            Validates Twilio configuration (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM).
        
        Side Effects:
            - Logs message SID for tracking
            - Calls Twilio REST API synchronously (via asyncio.to_thread)
        
        Args:
            to: String! (Recipient phone number, will be auto-formatted with "whatsapp:" prefix)
            message: String! (Message body text)
            
        Returns:
            WhatsAppMessageResponse with fields:
            - sid: String! (Twilio message SID, e.g., "SMxxxxxxxxxxxx")
            - status: String! (Message status, e.g., "queued", "sent", "delivered")
            - to: String! (Formatted recipient number, e.g., "whatsapp:+919800000001")
            - timestamp: String! (ISO timestamp when message was sent)
            - delivered: Boolean! (True if status in ["delivered","sent","read"])
            
        Raises:
            ValueError: If Twilio configuration is missing or message sending fails
        """
        try:
            from app.notifications import send_whatsapp_message
            
            # Validate inputs
            if not to or not to.strip():
                raise ValueError("Phone number (to) is required")
            if not message or not message.strip():
                raise ValueError("Message body is required")
            
            # Send WhatsApp message
            result = await send_whatsapp_message(
                to=to.strip(),
                body=message.strip()
            )
            
            return WhatsAppMessageResponse(
                sid=result["sid"],
                status=result["status"],
                to=result["to"],
                timestamp=result["timestamp"],
                delivered=result["delivered"]
            )
            
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise ValueError(f"Failed to send WhatsApp message: {str(e)}")


schema = strawberry.Schema(query=Query, mutation=Mutation)

