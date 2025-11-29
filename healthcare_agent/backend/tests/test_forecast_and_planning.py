"""Tests for forecasting and planning logic."""
import pytest
from bson import ObjectId

from app.forecast import run_forecast_for_camp, compute_lambda_from_historical, simulate_historical_counts
from app.planner import plan_assignments, calculate_unfilled_slots
from app.models import Camp, Volunteer, Requirement


class TestForecasting:
    """Test cases for volunteer demand forecasting."""
    
    def test_simulate_historical_counts(self):
        """Test historical count simulation."""
        counts = simulate_historical_counts(base_count=5, num_samples=10)
        
        assert len(counts) == 10
        assert all(isinstance(c, int) for c in counts)
        assert all(c >= 0 for c in counts)
        # First sample should be base_count
        assert counts[0] == 5
    
    def test_compute_lambda_from_historical(self):
        """Test lambda computation from historical counts."""
        historical = [5, 6, 4, 5, 7]
        lambda_param = compute_lambda_from_historical(historical)
        
        assert lambda_param > 0
        # Lambda should be close to mean of historical
        assert 4.0 <= lambda_param <= 7.0
    
    def test_compute_lambda_empty_list(self):
        """Test lambda computation with empty list."""
        lambda_param = compute_lambda_from_historical([])
        
        # Should return default value
        assert lambda_param == 1.0
    
    @pytest.mark.asyncio
    async def test_run_forecast_for_camp(self):
        """Test running forecast for a camp."""
        camp = Camp(
            id=ObjectId(),
            name="Test Camp",
            location="Test Location",
            start="2025-12-01T09:00:00Z",
            end="2025-12-01T17:00:00Z",
            requirements=[
                Requirement(role="doctor", count=2, slot="morning"),
                Requirement(role="nurse", count=3, slot="morning")
            ]
        )
        
        results = await run_forecast_for_camp(camp)
        
        assert len(results) == 2
        assert all(r.mean > 0 for r in results)
        assert all(r.upper_90 >= r.mean for r in results)
        assert all(r.lower_10 >= 0 for r in results)


class TestPlanning:
    """Test cases for volunteer assignment planning."""
    
    @pytest.mark.asyncio
    async def test_plan_assignments_simple(self):
        """Test basic assignment planning."""
        camp = Camp(
            id=ObjectId(),
            name="Test Camp",
            location="Test Location",
            start="2025-12-01T09:00:00Z",
            end="2025-12-01T17:00:00Z",
            requirements=[
                Requirement(role="doctor", count=1, slot="morning")
            ]
        )
        
        volunteers = [
            Volunteer(
                id=ObjectId(),
                name="Dr. Smith",
                phone="+919800000001",
                skills=["doctor"],
                availability=[
                    {"date": "2025-12-01", "slots": ["morning"]}
                ],
                no_show_rate=0.1
            )
        ]
        
        assignments = await plan_assignments(camp, volunteers)
        
        # Should have at least confirmed + new assignments
        assert len(assignments) >= 1
        # First assignment should be for the doctor role
        assert any(a.role == "doctor" for a in assignments)
    
    def test_calculate_unfilled_slots(self):
        """Test unfilled slots calculation."""
        requirements = [
            Requirement(role="doctor", count=2, slot="morning"),
            Requirement(role="nurse", count=3, slot="morning")
        ]
        
        from app.models import Assignment
        from datetime import datetime
        
        assignments = [
            Assignment(
                id=ObjectId(),
                camp_id=ObjectId(),
                volunteer_id=ObjectId(),
                role="doctor",
                slot="morning",
                status="assigned",
                is_backup=False,
                created_at=datetime.utcnow()
            )
        ]
        
        unfilled = calculate_unfilled_slots(requirements, assignments)
        
        # Required: 2 doctors + 3 nurses = 5, Assigned: 1 doctor = 4 unfilled
        assert unfilled == 4
    
    @pytest.mark.asyncio
    async def test_plan_with_no_eligible_volunteers(self):
        """Test planning when no volunteers are eligible."""
        camp = Camp(
            id=ObjectId(),
            name="Test Camp",
            location="Test Location",
            start="2025-12-01T09:00:00Z",
            end="2025-12-01T17:00:00Z",
            requirements=[
                Requirement(role="surgeon", count=1, slot="morning")
            ]
        )
        
        volunteers = [
            Volunteer(
                id=ObjectId(),
                name="Nurse Jane",
                phone="+919800000002",
                skills=["nurse"],  # Not a surgeon
                availability=[
                    {"date": "2025-12-01", "slots": ["morning"]}
                ],
                no_show_rate=0.1
            )
        ]
        
        assignments = await plan_assignments(camp, volunteers)
        
        # Should return empty or only confirmed assignments
        assert len(assignments) == 0

