"""
🤖 LLM-Powered Intelligent Volunteer Queueing System

This module implements an AI-powered volunteer prioritization queue that runs
BEFORE the OR-Tools optimizer. It uses Large Language Models to:

1. Analyze volunteer profiles and requirements
2. Generate intelligent priority scores
3. Create optimized volunteer queues
4. Provide explanations for assignments

WORKFLOW:
  Volunteers → LLM Analysis → Priority Queue → OR-Tools Optimizer → Assignments

This enhances the traditional constraint-based optimization with AI intelligence.
"""

import logging
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
from datetime import datetime

from app.models import Volunteer, Camp, Requirement, Assignment
from app.llm_service import get_llm_service

logger = logging.getLogger(__name__)


@dataclass
class QueuedVolunteer:
    """Volunteer with LLM-generated priority score in the queue."""
    volunteer: Volunteer
    priority_score: float
    requirement_match: Requirement
    explanation: str = ""
    
    def __lt__(self, other):
        """For sorting by priority (higher score = higher priority)."""
        return self.priority_score > other.priority_score


class LLMVolunteerQueue:
    """
    🌟 INTELLIGENT VOLUNTEER QUEUE powered by LLM
    
    This class manages the volunteer queueing process with AI-driven prioritization.
    It sits between volunteer pool and the OR-Tools optimizer, enhancing assignments
    with machine learning intelligence.
    """
    
    def __init__(self, camp: Camp, enable_llm: bool = True):
        """
        Initialize the intelligent queue for a camp.
        
        Args:
            camp: The camp to create assignments for
            enable_llm: Whether to use LLM (True) or fallback to heuristics (False)
        """
        self.camp = camp
        self.enable_llm = enable_llm
        self.llm_service = get_llm_service()
        self.queues: Dict[Tuple[str, str], List[QueuedVolunteer]] = {}
        
        # Metrics
        self.volunteers_analyzed = 0
        self.llm_calls_made = 0
        self.total_processing_time = 0.0
    
    async def build_intelligent_queues(
        self,
        volunteers: List[Volunteer],
        requirements: List[Requirement],
        existing_assignments: List[Assignment] = None
    ) -> None:
        """
        🚀 BUILD INTELLIGENT QUEUES - Core LLM Integration Point
        
        For each requirement, analyze all eligible volunteers using LLM and create
        a priority-sorted queue.
        
        Args:
            volunteers: Pool of available volunteers
            requirements: Requirements to fill
            existing_assignments: Already confirmed assignments to consider
        """
        start_time = datetime.now()
        
        if existing_assignments is None:
            existing_assignments = []
        
        # Get confirmed volunteer IDs (they're already assigned)
        confirmed_volunteer_ids = {
            str(assign.volunteer_id)
            for assign in existing_assignments
            if assign.status == "confirmed"
        }
        
        logger.info(
            f"🤖 Starting LLM-powered queue building for {len(requirements)} requirements "
            f"with {len(volunteers)} volunteers"
        )
        
        # Build queue for each requirement
        for requirement in requirements:
            await self._build_queue_for_requirement(
                requirement,
                volunteers,
                confirmed_volunteer_ids,
                existing_assignments
            )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        self.total_processing_time = processing_time
        
        logger.info(
            f"✅ LLM Queue building complete in {processing_time:.2f}s\n"
            f"   - Volunteers analyzed: {self.volunteers_analyzed}\n"
            f"   - LLM API calls: {self.llm_calls_made}\n"
            f"   - Queues created: {len(self.queues)}"
        )
    
    async def _build_queue_for_requirement(
        self,
        requirement: Requirement,
        volunteers: List[Volunteer],
        confirmed_volunteer_ids: Set[str],
        existing_assignments: List[Assignment]
    ) -> None:
        """Build priority queue for a single requirement using LLM."""
        
        # Filter eligible volunteers (not confirmed elsewhere, has skills, available)
        eligible_volunteers = [
            v for v in volunteers
            if str(v.id) not in confirmed_volunteer_ids
            and self._is_volunteer_eligible(v, requirement)
        ]
        
        if not eligible_volunteers:
            logger.warning(
                f"No eligible volunteers for {requirement.role} in {requirement.slot}"
            )
            self.queues[(requirement.role, requirement.slot)] = []
            return
        
        # Use LLM to generate priority scores
        if self.enable_llm and self.llm_service.is_available():
            try:
                priority_scores = await self.llm_service.generate_volunteer_priority_scores(
                    eligible_volunteers,
                    requirement,
                    self.camp,
                    existing_assignments
                )
                self.llm_calls_made += 1
                logger.info(
                    f"   🧠 LLM analyzed {len(eligible_volunteers)} volunteers "
                    f"for {requirement.role}/{requirement.slot}"
                )
            except Exception as e:
                logger.error(f"LLM scoring failed, using fallback: {e}")
                priority_scores = self._fallback_scoring(eligible_volunteers, requirement)
        else:
            priority_scores = self._fallback_scoring(eligible_volunteers, requirement)
        
        # Create queued volunteers with scores
        queued_volunteers = []
        for volunteer in eligible_volunteers:
            score = priority_scores.get(str(volunteer.id), 0.5)
            
            queued_volunteer = QueuedVolunteer(
                volunteer=volunteer,
                priority_score=score,
                requirement_match=requirement
            )
            queued_volunteers.append(queued_volunteer)
            self.volunteers_analyzed += 1
        
        # Sort by priority (highest first)
        queued_volunteers.sort()
        
        # Store queue
        key = (requirement.role, requirement.slot)
        self.queues[key] = queued_volunteers
        
        logger.debug(
            f"   Queue created for {requirement.role}/{requirement.slot}: "
            f"{len(queued_volunteers)} volunteers, "
            f"top score: {queued_volunteers[0].priority_score:.2f if queued_volunteers else 0}"
        )
    
    def _is_volunteer_eligible(
        self,
        volunteer: Volunteer,
        requirement: Requirement
    ) -> bool:
        """Check if volunteer is eligible for a requirement."""
        # Check skill match
        if requirement.role not in volunteer.skills:
            return False
        
        # Check availability
        for avail in volunteer.availability:
            if requirement.slot in avail.slots:
                return True
        
        return False
    
    def _fallback_scoring(
        self,
        volunteers: List[Volunteer],
        requirement: Requirement
    ) -> Dict[str, float]:
        """Simple heuristic scoring when LLM is not available."""
        scores = {}
        for volunteer in volunteers:
            score = 0.5  # Base score
            
            # Exact skill match: +0.3
            if requirement.role in volunteer.skills:
                score += 0.3
            
            # High reliability: +0.2
            reliability = 1.0 - volunteer.no_show_rate
            score += reliability * 0.2
            
            scores[str(volunteer.id)] = min(1.0, score)
        
        return scores
    
    def get_top_volunteers(
        self,
        requirement: Requirement,
        count: int = 10
    ) -> List[QueuedVolunteer]:
        """
        Get top N volunteers from queue for a requirement.
        
        Args:
            requirement: The requirement to get volunteers for
            count: Number of top volunteers to return
            
        Returns:
            List of top QueuedVolunteer objects sorted by priority
        """
        key = (requirement.role, requirement.slot)
        queue = self.queues.get(key, [])
        return queue[:count]
    
    def get_all_queues(self) -> Dict[Tuple[str, str], List[QueuedVolunteer]]:
        """Get all volunteer queues."""
        return self.queues
    
    def get_queue_summary(self) -> Dict[str, any]:
        """Get summary statistics about the queues."""
        total_volunteers = sum(len(queue) for queue in self.queues.values())
        
        avg_scores = {}
        for key, queue in self.queues.items():
            if queue:
                avg_score = sum(qv.priority_score for qv in queue) / len(queue)
                avg_scores[f"{key[0]}_{key[1]}"] = round(avg_score, 3)
        
        return {
            "total_queues": len(self.queues),
            "total_volunteers_queued": total_volunteers,
            "volunteers_analyzed": self.volunteers_analyzed,
            "llm_calls_made": self.llm_calls_made,
            "processing_time_seconds": round(self.total_processing_time, 2),
            "average_scores_by_requirement": avg_scores,
            "llm_enabled": self.enable_llm and self.llm_service.is_available()
        }
    
    async def generate_assignment_explanations(
        self,
        assignments: List[Assignment]
    ) -> Dict[str, str]:
        """
        Generate AI explanations for assignments.
        
        Args:
            assignments: List of assignments to explain
            
        Returns:
            Dictionary mapping assignment_id -> explanation
        """
        if not self.enable_llm or not self.llm_service.is_available():
            return {}
        
        explanations = {}
        
        for assignment in assignments:
            try:
                # Find the queued volunteer info
                key = (assignment.role, assignment.slot)
                queue = self.queues.get(key, [])
                
                queued_vol = None
                for qv in queue:
                    if qv.volunteer.id == assignment.volunteer_id:
                        queued_vol = qv
                        break
                
                if queued_vol:
                    # Generate explanation using LLM
                    explanation = await self.llm_service.generate_assignment_explanation(
                        queued_vol.volunteer,
                        queued_vol.requirement_match,
                        self.camp,
                        queued_vol.priority_score
                    )
                    explanations[str(assignment.id)] = explanation
                    
            except Exception as e:
                logger.error(f"Failed to generate explanation for assignment {assignment.id}: {e}")
        
        return explanations


async def create_intelligent_volunteer_queue(
    camp: Camp,
    volunteers: List[Volunteer],
    requirements: List[Requirement],
    existing_assignments: List[Assignment] = None,
    enable_llm: bool = True
) -> LLMVolunteerQueue:
    """
    🌟 MAIN ENTRY POINT: Create an intelligent volunteer queue using LLM
    
    This is the primary function to call when you want to use LLM-powered
    volunteer prioritization in your planning workflow.
    
    Args:
        camp: The camp to plan for
        volunteers: Available volunteer pool
        requirements: Requirements to fill
        existing_assignments: Already confirmed assignments
        enable_llm: Whether to use LLM (True) or fallback heuristics (False)
        
    Returns:
        LLMVolunteerQueue with sorted, prioritized volunteers
        
    Example:
        queue = await create_intelligent_volunteer_queue(
            camp=my_camp,
            volunteers=all_volunteers,
            requirements=my_camp.requirements,
            enable_llm=True
        )
        
        # Get top 5 volunteers for a requirement
        top_volunteers = queue.get_top_volunteers(requirement, count=5)
    """
    queue = LLMVolunteerQueue(camp, enable_llm=enable_llm)
    await queue.build_intelligent_queues(volunteers, requirements, existing_assignments)
    return queue

