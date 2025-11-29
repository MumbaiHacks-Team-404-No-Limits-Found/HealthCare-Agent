"""
LLM Service for Intelligent Volunteer Queueing and Assignment

This module provides LLM-powered intelligence for volunteer assignment:
- Volunteer priority scoring based on skills, availability, and history
- Natural language explanations for assignments
- Intelligent matching recommendations

Supports:
- OpenAI GPT-4/GPT-3.5
- Anthropic Claude (optional)
"""

import logging
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from app.models import Volunteer, Camp, Requirement, Assignment
from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM-based volunteer analysis and prioritization."""
    
    def __init__(self):
        """Initialize LLM service with API keys from config."""
        self.openai_api_key = getattr(settings, 'openai_api_key', '')
        self.anthropic_api_key = getattr(settings, 'anthropic_api_key', '')
        self.llm_provider = getattr(settings, 'llm_provider', 'openai')  # 'openai' or 'anthropic'
        self.llm_model = getattr(settings, 'llm_model', 'gpt-3.5-turbo')
        
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the LLM client based on provider."""
        if not self.openai_api_key and not self.anthropic_api_key:
            logger.warning(
                "No LLM API keys configured. LLM features will be disabled. "
                "Set OPENAI_API_KEY or ANTHROPIC_API_KEY in environment."
            )
            return
        
        try:
            if self.llm_provider == 'openai' and self.openai_api_key:
                import openai
                self.client = openai.OpenAI(api_key=self.openai_api_key)
                logger.info(f"✅ LLM Service initialized with OpenAI ({self.llm_model})")
            elif self.llm_provider == 'anthropic' and self.anthropic_api_key:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.anthropic_api_key)
                logger.info(f"✅ LLM Service initialized with Anthropic Claude")
            else:
                logger.warning("LLM provider not properly configured")
        except ImportError as e:
            logger.error(f"Failed to import LLM library: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
    
    def is_available(self) -> bool:
        """Check if LLM service is available."""
        return self.client is not None
    
    async def generate_volunteer_priority_scores(
        self,
        volunteers: List[Volunteer],
        requirement: Requirement,
        camp: Camp,
        existing_assignments: List[Assignment] = None
    ) -> Dict[str, float]:
        """
        Generate intelligent priority scores for volunteers using LLM.
        
        🌟 HIGHLIGHTED: This is the core LLM integration for volunteer queueing!
        
        The LLM analyzes:
        - Volunteer skills matching the role
        - Availability for the specific slot
        - Historical no-show rates
        - Camp context and requirements
        
        Args:
            volunteers: List of available volunteers
            requirement: The specific requirement to fill
            camp: The camp details
            existing_assignments: Existing assignments to consider
            
        Returns:
            Dictionary mapping volunteer_id -> priority_score (0.0 to 1.0)
            Higher scores = higher priority
        """
        if not self.is_available():
            logger.warning("LLM not available, using default scoring")
            return self._fallback_priority_scores(volunteers, requirement)
        
        try:
            # Prepare context for LLM
            prompt = self._build_prioritization_prompt(
                volunteers, requirement, camp, existing_assignments
            )
            
            # Call LLM
            if self.llm_provider == 'openai':
                response = await self._call_openai(prompt)
            else:
                response = await self._call_anthropic(prompt)
            
            # Parse LLM response to extract scores
            scores = self._parse_priority_scores(response, volunteers)
            
            logger.info(
                f"🤖 LLM generated priority scores for {len(scores)} volunteers "
                f"for {requirement.role} in {requirement.slot}"
            )
            
            return scores
            
        except Exception as e:
            logger.error(f"LLM priority scoring failed: {e}", exc_info=True)
            return self._fallback_priority_scores(volunteers, requirement)
    
    def _build_prioritization_prompt(
        self,
        volunteers: List[Volunteer],
        requirement: Requirement,
        camp: Camp,
        existing_assignments: List[Assignment] = None
    ) -> str:
        """Build the prompt for volunteer prioritization."""
        
        # Format volunteer data
        volunteer_data = []
        for v in volunteers:
            volunteer_data.append({
                "id": str(v.id),
                "name": v.name,
                "skills": v.skills,
                "availability_slots": [
                    f"{avail.date}: {', '.join(avail.slots)}"
                    for avail in v.availability
                ],
                "no_show_rate": v.no_show_rate,
                "reliability_score": 1.0 - v.no_show_rate
            })
        
        prompt = f"""You are an AI assistant for medical camp volunteer coordination. Your task is to analyze volunteers and assign priority scores for an upcoming assignment.

**Camp Details:**
- Name: {camp.name}
- Location: {camp.location}
- Date: {camp.start} to {camp.end}

**Requirement to Fill:**
- Role: {requirement.role}
- Time Slot: {requirement.slot}
- Positions Needed: {requirement.count}

**Available Volunteers:**
{json.dumps(volunteer_data, indent=2)}

**Your Task:**
Analyze each volunteer and assign a priority score from 0.0 to 1.0 based on:
1. **Skill Match** (40%): How well their skills match the required role
2. **Availability** (30%): Whether they're available for the specific slot
3. **Reliability** (20%): Based on their no-show rate history
4. **Suitability** (10%): Overall fit for this camp's context

**Output Format (JSON only, no explanation):**
{{
  "volunteer_id": priority_score,
  ...
}}

Example:
{{
  "507f1f77bcf86cd799439011": 0.95,
  "507f1f77bcf86cd799439012": 0.72,
  "507f1f77bcf86cd799439013": 0.45
}}

Return ONLY the JSON object with volunteer IDs and their priority scores."""
        
        return prompt
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant specialized in healthcare volunteer coordination and assignment optimization."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent scoring
                max_tokens=1000,
                response_format={"type": "json_object"}  # Force JSON output (GPT-4 Turbo)
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API."""
        try:
            message = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return message.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise
    
    def _parse_priority_scores(
        self,
        llm_response: str,
        volunteers: List[Volunteer]
    ) -> Dict[str, float]:
        """Parse LLM response to extract priority scores."""
        try:
            # Extract JSON from response
            response_text = llm_response.strip()
            
            # Handle markdown code blocks
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])
            
            # Parse JSON
            scores_dict = json.loads(response_text)
            
            # Validate and normalize scores
            validated_scores = {}
            for volunteer in volunteers:
                volunteer_id = str(volunteer.id)
                score = scores_dict.get(volunteer_id, 0.5)  # Default to medium priority
                
                # Ensure score is between 0 and 1
                score = max(0.0, min(1.0, float(score)))
                validated_scores[volunteer_id] = score
            
            return validated_scores
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.debug(f"Response was: {llm_response}")
            raise
        except Exception as e:
            logger.error(f"Failed to parse priority scores: {e}")
            raise
    
    def _fallback_priority_scores(
        self,
        volunteers: List[Volunteer],
        requirement: Requirement
    ) -> Dict[str, float]:
        """
        Fallback scoring when LLM is not available.
        
        Uses simple heuristics:
        - Has required skill: +0.6
        - Available for slot: +0.3
        - High reliability (low no-show): +0.1
        """
        scores = {}
        
        for volunteer in volunteers:
            score = 0.0
            
            # Skill match
            if requirement.role in volunteer.skills:
                score += 0.6
            
            # Availability check
            for avail in volunteer.availability:
                if requirement.slot in avail.slots:
                    score += 0.3
                    break
            
            # Reliability
            reliability = 1.0 - volunteer.no_show_rate
            score += reliability * 0.1
            
            scores[str(volunteer.id)] = min(1.0, score)
        
        return scores
    
    async def generate_assignment_explanation(
        self,
        volunteer: Volunteer,
        requirement: Requirement,
        camp: Camp,
        priority_score: float
    ) -> str:
        """
        Generate natural language explanation for why a volunteer was assigned.
        
        Args:
            volunteer: The assigned volunteer
            requirement: The requirement they were assigned to
            camp: The camp details
            priority_score: Their computed priority score
            
        Returns:
            Human-readable explanation string
        """
        if not self.is_available():
            return self._fallback_explanation(volunteer, requirement, priority_score)
        
        try:
            prompt = f"""Explain briefly (2-3 sentences) why this volunteer is a good match for this assignment:

Volunteer: {volunteer.name}
Skills: {', '.join(volunteer.skills)}
Reliability: {(1.0 - volunteer.no_show_rate) * 100:.0f}%
Priority Score: {priority_score:.2f}/1.0

Assignment:
Role: {requirement.role}
Slot: {requirement.slot}
Camp: {camp.name} at {camp.location}

Write a concise, professional explanation suitable for administrators."""
            
            if self.llm_provider == 'openai':
                response = await self._call_openai(prompt)
            else:
                response = await self._call_anthropic(prompt)
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate explanation: {e}")
            return self._fallback_explanation(volunteer, requirement, priority_score)
    
    def _fallback_explanation(
        self,
        volunteer: Volunteer,
        requirement: Requirement,
        priority_score: float
    ) -> str:
        """Fallback explanation generation."""
        has_skill = requirement.role in volunteer.skills
        reliability = (1.0 - volunteer.no_show_rate) * 100
        
        if has_skill:
            return (
                f"{volunteer.name} was assigned with a priority score of {priority_score:.2f}. "
                f"They have the required '{requirement.role}' skill and a {reliability:.0f}% reliability rate."
            )
        else:
            return (
                f"{volunteer.name} was assigned with a priority score of {priority_score:.2f}. "
                f"While they don't have the exact role listed, they have relevant experience "
                f"and a {reliability:.0f}% reliability rate."
            )


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create singleton LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service

