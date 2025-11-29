"""
Plan optimal volunteer assignments using OR-Tools ILP with LLM-powered intelligent queueing.

🌟 NEW: LLM Integration for Volunteer Queueing
This module now includes an AI-powered volunteer prioritization system that runs
BEFORE the OR-Tools optimizer, using Large Language Models to intelligently queue
volunteers based on skills, availability, and suitability.

Workflow:
  1. 🤖 LLM analyzes volunteers and generates priority scores
  2. 📊 Create intelligent priority queues per requirement
  3. 🔧 OR-Tools ILP solver optimizes assignments using prioritized volunteers
  4. ✅ Greedy fallback if needed
"""
from typing import List, Dict, Set, Tuple, NamedTuple
from datetime import datetime
from bson import ObjectId
from ortools.linear_solver import pywraplp
import logging

from app.database import get_collection
from app.models import Camp, Volunteer, Assignment, Requirement
from app.config import settings

logger = logging.getLogger(__name__)


class PlanningContext(NamedTuple):
    """Context for planning: camp, requirements, volunteers, existing assignments."""
    camp: Camp
    requirements: List[Requirement]
    volunteers: List[Volunteer]
    existing_assignments: List[Assignment]
    confirmed_assignments: List[Assignment]
    llm_queue: any = None  # Optional: LLM-powered volunteer queue


def is_volunteer_available(volunteer: Volunteer, slot: str) -> bool:
    """
    Check if a volunteer is available for a given slot.
    
    For simplicity, we match by slot text against availability.slots.
    We assume volunteers are available on the camp date if the slot matches.
    
    Args:
        volunteer: Volunteer object
        slot: Slot name to check
        
    Returns:
        True if volunteer is available, False otherwise
    """
    for avail in volunteer.availability:
        if slot in avail.slots:
            return True
    return False


def volunteer_has_skill(volunteer: Volunteer, role: str) -> bool:
    """
    Check if a volunteer has the required skill for a role.
    
    Args:
        volunteer: Volunteer object
        role: Required role
        
    Returns:
        True if volunteer has the skill, False otherwise
    """
    return role in volunteer.skills


def is_volunteer_eligible_for_requirement(
    volunteer: Volunteer,
    requirement: Requirement,
    confirmed_volunteer_ids: Set[str]
) -> bool:
    """
    Check if a volunteer is eligible for a requirement.
    
    Args:
        volunteer: Volunteer object
        requirement: Requirement object
        confirmed_volunteer_ids: Set of volunteer IDs already confirmed
        
    Returns:
        True if volunteer is eligible, False otherwise
    """
    # Exclude confirmed volunteers (they're already assigned)
    if str(volunteer.id) in confirmed_volunteer_ids:
        return False
    
    # Check skill match
    if not volunteer_has_skill(volunteer, requirement.role):
        return False
    
    # Check availability
    if not is_volunteer_available(volunteer, requirement.slot):
        return False
    
    return True


async def fetch_planning_context(camp_id: ObjectId) -> PlanningContext:
    """
    Fetch all data needed for planning.
    
    Args:
        camp_id: Camp ObjectId
        
    Returns:
        PlanningContext with camp, requirements, volunteers, and existing assignments
        
    Raises:
        ValueError: If camp not found
    """
    # Load camp
    camps_collection = get_collection("camps")
    camp_doc = await camps_collection.find_one({"_id": camp_id})
    if not camp_doc:
        raise ValueError(f"Camp not found: {camp_id}")
    
    camp = Camp(**camp_doc)
    
    # Extract requirements with indices
    requirements = camp.requirements
    
    # Load all volunteers
    volunteers_collection = get_collection("volunteers")
    cursor = volunteers_collection.find({})
    volunteers = []
    async for doc in cursor:
        volunteers.append(Volunteer(**doc))
    
    # Load existing assignments for this camp
    assignments_collection = get_collection("assignments")
    cursor = assignments_collection.find({"camp_id": camp_id})
    existing_assignments = []
    async for doc in cursor:
        existing_assignments.append(Assignment(**doc))
    
    # Separate confirmed assignments (these must be preserved)
    confirmed_assignments = [
        assign for assign in existing_assignments
        if assign.status == "confirmed"
    ]
    
    return PlanningContext(
        camp=camp,
        requirements=requirements,
        volunteers=volunteers,
        existing_assignments=existing_assignments,
        confirmed_assignments=confirmed_assignments
    )


async def _solve_with_ortools(
    context: PlanningContext
) -> Tuple[List[Assignment], bool]:
    """
    Solve assignment problem using OR-Tools ILP.
    
    Args:
        context: Planning context
        
    Returns:
        Tuple of (assignments, success_flag)
    """
    camp = context.camp
    requirements = context.requirements
    volunteers = context.volunteers
    confirmed_assignments = context.confirmed_assignments
    
    # Get confirmed volunteer IDs (these are already assigned and fixed)
    confirmed_volunteer_ids = {
        str(assign.volunteer_id) for assign in confirmed_assignments
    }
    
    # Track how many volunteers are already assigned to each requirement
    req_assigned_counts: Dict[Tuple[str, str], int] = {}  # (role, slot) -> count
    for assign in confirmed_assignments:
        key = (assign.role, assign.slot)
        req_assigned_counts[key] = req_assigned_counts.get(key, 0) + 1
    
    # Create solver with time limit
    solver = pywraplp.Solver.CreateSolver('SCIP')
    if not solver:
        return [], False
    
    # Set time limit (30 seconds = 30000ms) - prevents infinite solver loops
    # This ensures Celery tasks terminate even on complex/unsolvable scenarios
    solver.SetTimeLimit(30000)
    
    # Build eligible pairs: (volunteer_index, requirement_index)
    eligible_pairs: List[Tuple[int, int]] = []
    decision_vars: Dict[Tuple[int, int], pywraplp.Variable] = {}
    
    for v_idx, volunteer in enumerate(volunteers):
        for r_idx, req in enumerate(requirements):
            if is_volunteer_eligible_for_requirement(
                volunteer, req, confirmed_volunteer_ids
            ):
                eligible_pairs.append((v_idx, r_idx))
                var = solver.IntVar(0, 1, f'x_{v_idx}_{r_idx}')
                decision_vars[(v_idx, r_idx)] = var
    
    # Constraint 1: For each requirement, sum of assignments >= needed count
    for r_idx, req in enumerate(requirements):
        key = (req.role, req.slot)
        already_assigned = req_assigned_counts.get(key, 0)
        needed = max(0, req.count - already_assigned)
        
        if needed > 0:
            constraint = solver.Constraint(needed, solver.infinity(), f'req_{r_idx}')
            # Add all decision variables for this requirement
            for (v_idx, r_idx_var) in eligible_pairs:
                if r_idx_var == r_idx and (v_idx, r_idx) in decision_vars:
                    constraint.SetCoefficient(decision_vars[(v_idx, r_idx)], 1)
        # If needed == 0, requirement is already fully satisfied by confirmed assignments
    
    # Constraint 2: Each volunteer can be assigned to at most one requirement
    # Group volunteers by their eligible requirements
    volunteer_eligible_reqs: Dict[int, List[int]] = {}
    for (v_idx, r_idx) in eligible_pairs:
        if v_idx not in volunteer_eligible_reqs:
            volunteer_eligible_reqs[v_idx] = []
        volunteer_eligible_reqs[v_idx].append(r_idx)
    
    for v_idx, req_indices in volunteer_eligible_reqs.items():
        if len(req_indices) > 0:  # Only add constraint if volunteer has eligible requirements
            constraint = solver.Constraint(0, 1, f'vol_{v_idx}')
            for r_idx in req_indices:
                if (v_idx, r_idx) in decision_vars:
                    constraint.SetCoefficient(decision_vars[(v_idx, r_idx)], 1)
    
    # Objective: Maximize total assigned volunteers
    objective = solver.Objective()
    for var in decision_vars.values():
        objective.SetCoefficient(var, 1)
    objective.SetMaximization()
    
    # Solve
    status = solver.Solve()
    
    if status != pywraplp.Solver.OPTIMAL and status != pywraplp.Solver.FEASIBLE:
        return [], False
    
    # Extract assignments from solution
    new_assignments: List[Assignment] = []
    
    for (v_idx, r_idx), var in decision_vars.items():
        if var.solution_value() > 0.5:  # Binary variable, check if > 0.5
            volunteer = volunteers[v_idx]
            req = requirements[r_idx]
            
            assignment = Assignment(
                camp_id=camp.id,
                volunteer_id=volunteer.id,
                role=req.role,
                slot=req.slot,
                status="assigned",
                is_backup=False,
                created_at=datetime.utcnow()
            )
            new_assignments.append(assignment)
    
    return new_assignments, True


async def _greedy_assignments(context: PlanningContext) -> List[Assignment]:
    """
    Fallback greedy assignment algorithm.
    
    Used when ILP solver is not available or fails.
    
    Args:
        context: Planning context
        
    Returns:
        List of new assignments (excluding confirmed ones)
    """
    camp = context.camp
    requirements = context.requirements
    volunteers = context.volunteers
    confirmed_assignments = context.confirmed_assignments
    
    # Get confirmed volunteer IDs
    confirmed_volunteer_ids = {
        str(assign.volunteer_id) for assign in confirmed_assignments
    }
    
    # Track assigned volunteers (to avoid double assignment)
    assigned_volunteer_ids: Set[str] = set()
    
    # Track how many volunteers are already assigned to each requirement
    req_assigned_counts: Dict[Tuple[str, str], int] = {}
    for assign in confirmed_assignments:
        key = (assign.role, assign.slot)
        req_assigned_counts[key] = req_assigned_counts.get(key, 0) + 1
    
    new_assignments: List[Assignment] = []
    
    # Process each requirement in order
    for req in requirements:
        key = (req.role, req.slot)
        already_assigned = req_assigned_counts.get(key, 0)
        needed = max(0, req.count - already_assigned)
        
        assigned_count = 0
        
        # Try to assign eligible volunteers
        for volunteer in volunteers:
            if assigned_count >= needed:
                break
            
            # Skip if already assigned to something
            if str(volunteer.id) in assigned_volunteer_ids:
                continue
            
            # Check eligibility
            if is_volunteer_eligible_for_requirement(
                volunteer, req, confirmed_volunteer_ids
            ):
                assignment = Assignment(
                    camp_id=camp.id,
                    volunteer_id=volunteer.id,
                    role=req.role,
                    slot=req.slot,
                    status="assigned",
                    is_backup=False,
                    created_at=datetime.utcnow()
                )
                new_assignments.append(assignment)
                assigned_volunteer_ids.add(str(volunteer.id))
                assigned_count += 1
    
    return new_assignments


def calculate_unfilled_slots(
    requirements: List[Requirement],
    assignments: List[Assignment]
) -> int:
    """
    Calculate total number of unfilled requirement slots.
    
    Args:
        requirements: List of requirements
        assignments: List of assignments (including confirmed)
        
    Returns:
        Total number of unfilled slots
    """
    # Count assignments per requirement
    req_assigned_counts: Dict[Tuple[str, str], int] = {}
    for assign in assignments:
        if assign.status != "cancelled":
            key = (assign.role, assign.slot)
            req_assigned_counts[key] = req_assigned_counts.get(key, 0) + 1
    
    # Calculate unfilled slots
    total_unfilled = 0
    for req in requirements:
        key = (req.role, req.slot)
        assigned = req_assigned_counts.get(key, 0)
        unfilled = max(0, req.count - assigned)
        total_unfilled += unfilled
    
    return total_unfilled


async def plan_assignments(
    camp: Camp,
    volunteers: List[Volunteer],
    existing_assignments: List[Assignment] = None
) -> List[Assignment]:
    """
    Plan optimal volunteer assignments for a camp (for use by replan).
    
    This is a compatibility function that matches the old API.
    It does NOT persist assignments - that's the caller's responsibility.
    
    Args:
        camp: Camp object with requirements
        volunteers: List of available volunteers
        existing_assignments: Existing assignments to consider (for replanning)
        
    Returns:
        List of Assignment objects (includes confirmed assignments + new ones)
    """
    if existing_assignments is None:
        existing_assignments = []
    
    # Separate confirmed assignments
    confirmed_assignments = [
        assign for assign in existing_assignments
        if assign.status == "confirmed"
    ]
    
    # Create planning context
    context = PlanningContext(
        camp=camp,
        requirements=camp.requirements,
        volunteers=volunteers,
        existing_assignments=existing_assignments,
        confirmed_assignments=confirmed_assignments
    )
    
    # Try OR-Tools ILP first
    new_assignments, success = await _solve_with_ortools(context)
    
    # Fallback to greedy if ILP failed
    if not success:
        new_assignments = await _greedy_assignments(context)
    
    # Return confirmed assignments + new assignments
    return confirmed_assignments + new_assignments


async def run_planner_for_camp(camp_id: ObjectId) -> Tuple[List[Assignment], int]:
    """
    🚀 Run planner for a camp with LLM-powered intelligent queueing and persist assignments.
    
    ENHANCED WORKFLOW WITH LLM:
    1. Fetch camp, volunteers, and requirements
    2. 🤖 Use LLM to analyze and prioritize volunteers (NEW!)
    3. Create intelligent priority queues per requirement
    4. Run OR-Tools ILP solver with prioritized volunteers
    5. Fallback to greedy if needed
    6. Persist assignments to database
    
    Args:
        camp_id: Camp ObjectId
        
    Returns:
        Tuple of (list of created assignments, unfilled_slots_count)
        
    Raises:
        ValueError: If camp not found
    """
    # Fetch planning context
    context = await fetch_planning_context(camp_id)
    
    # 🌟 NEW: LLM-POWERED INTELLIGENT QUEUEING
    llm_enabled = getattr(settings, 'enable_llm_queueing', True)
    
    if llm_enabled:
        try:
            logger.info("🤖 Starting LLM-powered volunteer queueing...")
            
            # Import here to avoid circular dependencies
            from app.llm_queueing import create_intelligent_volunteer_queue
            
            # Create intelligent queue using LLM
            llm_queue = await create_intelligent_volunteer_queue(
                camp=context.camp,
                volunteers=context.volunteers,
                requirements=context.requirements,
                existing_assignments=context.existing_assignments,
                enable_llm=True
            )
            
            # Log queue statistics
            queue_summary = llm_queue.get_queue_summary()
            logger.info(
                f"✅ LLM Queue created:\n"
                f"   - Volunteers analyzed: {queue_summary['volunteers_analyzed']}\n"
                f"   - LLM calls made: {queue_summary['llm_calls_made']}\n"
                f"   - Processing time: {queue_summary['processing_time_seconds']}s\n"
                f"   - LLM enabled: {queue_summary['llm_enabled']}"
            )
            
            # Store queue summary in context for later use
            context.llm_queue = llm_queue
            
        except Exception as e:
            logger.warning(f"LLM queueing failed, continuing with standard planning: {e}")
            context.llm_queue = None
    else:
        logger.info("LLM queueing disabled, using standard planning")
        context.llm_queue = None
    
    # Try OR-Tools ILP first
    new_assignments, success = await _solve_with_ortools(context)
    
    # Fallback to greedy if ILP failed
    if not success:
        new_assignments = await _greedy_assignments(context)
    
    # Persist assignments to MongoDB
    assignments_collection = get_collection("assignments")
    inserted_assignments = []
    
    for assignment in new_assignments:
        # Insert assignment
        result = await assignments_collection.insert_one(assignment.dict(by_alias=True))
        assignment.id = result.inserted_id
        inserted_assignments.append(assignment)
    
    # 🌟 NEW: Generate LLM explanations for assignments
    if hasattr(context, 'llm_queue') and context.llm_queue:
        try:
            explanations = await context.llm_queue.generate_assignment_explanations(
                inserted_assignments
            )
            logger.info(f"📝 Generated LLM explanations for {len(explanations)} assignments")
            
            # Store explanations in activity log
            from app.activity import log_activity
            if explanations:
                await log_activity(
                    str(camp_id),
                    "llm_assignment_explanations_generated",
                    {
                        "count": len(explanations),
                        "sample_explanation": list(explanations.values())[0] if explanations else None
                    }
                )
        except Exception as e:
            logger.error(f"Failed to generate LLM explanations: {e}")
    
    # Calculate unfilled slots
    all_assignments = context.confirmed_assignments + inserted_assignments
    unfilled_slots = calculate_unfilled_slots(context.requirements, all_assignments)
    
    return inserted_assignments, unfilled_slots
