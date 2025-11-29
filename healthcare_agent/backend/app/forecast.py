"""
Forecast volunteer demand using Poisson model.

This module uses real historical demand data from the role_demand_history collection
when available. If no matching historical data exists for a requirement, it falls back
to a deterministic simulation based on the requirement's base count.

MongoDB Collections:
    - role_demand_history: PRIMARY data source for historical demand counts
        * Queries by role (required) and slot (optional)
        * Extracts demand_count values from matching documents
    - camps: Fetches camp requirements for forecasting

Data Source Priority:
1. role_demand_history collection (real historical data) - PRIMARY
   - Queries by role and slot to find matching historical records
   - Computes lambda (mean) from historical demand_count values
2. Simulated historical counts (fallback when no real data available)
   - Deterministic pattern based on requirement.count
   - Used only when role_demand_history has no matching records

Forecasting Algorithm:
    For each requirement:
    1. Attempts to fetch real historical counts from role_demand_history
    2. If real data available: lambda = mean(historical_counts), clamped to >= 0.1
    3. If no real data: Uses simulated historical counts, then computes lambda
    4. Calculates Poisson percentiles using scipy.stats.poisson:
       - mean = lambda
       - upper90 = poisson.ppf(0.9, lambda) (90th percentile)
       - lower10 = poisson.ppf(0.1, lambda) (10th percentile)
    5. Ensures non-negative results
"""
from typing import List, Optional
import numpy as np
from scipy import stats

from app.models import Camp, ForecastResult
from app.database import get_collection


async def fetch_historical_counts_for_requirement(
    camp: Camp,
    role: str,
    slot: Optional[str] = None
) -> List[int]:
    """
    Fetch historical demand counts from role_demand_history collection.
    
    Queries the role_demand_history collection for matching records based on:
    - role (required)
    - slot (optional, if provided)
    - Optionally filters by camp location or type if available
    
    Args:
        camp: Camp object (for location/type filtering)
        role: Required role (e.g., "doctor", "nurse")
        slot: Optional slot filter (e.g., "morning", "afternoon")
        
    Returns:
        List of integer demand_count values from matching historical records.
        Returns empty list if no matching records found.
    """
    try:
        collection = get_collection("role_demand_history")
        
        # Build query filter
        query = {"role": role}
        
        # Add slot filter if provided
        if slot:
            query["slot"] = slot
        
        # Optionally filter by location or camp_type if available in history
        # (This assumes role_demand_history might have location/camp_type fields)
        # For now, we'll query by role and slot only
        
        # Execute query
        cursor = collection.find(query)
        
        historical_counts = []
        async for doc in cursor:
            demand_count = doc.get("demand_count")
            if demand_count is not None:
                try:
                    historical_counts.append(int(demand_count))
                except (ValueError, TypeError):
                    continue  # Skip invalid values
        
        return historical_counts
        
    except Exception as e:
        # Log error but don't fail - fall back to simulation
        print(f"Warning: Failed to fetch historical data for {role}/{slot}: {e}")
        return []


def simulate_historical_counts(base_count: int, num_samples: int = 10) -> List[int]:
    """
    Simulate historical volunteer counts for a requirement.
    
    Creates a deterministic list of historical counts around the base_count.
    In production, this would query actual historical data from past camps.
    
    Args:
        base_count: Base requirement count
        num_samples: Number of historical samples to generate
        
    Returns:
        List of historical count integers
    """
    # Generate deterministic historical counts around base_count
    # Pattern: [count, count+1, max(0, count-1), count+2, count-1, ...]
    historical = []
    
    for i in range(num_samples):
        if i == 0:
            historical.append(base_count)
        elif i == 1:
            historical.append(base_count + 1)
        elif i == 2:
            historical.append(max(0, base_count - 1))
        elif i == 3:
            historical.append(base_count + 2)
        elif i == 4:
            historical.append(max(0, base_count - 1))
        else:
            # Add some variance: base_count ± (i % 3 - 1)
            variance = (i % 3) - 1
            historical.append(max(0, base_count + variance))
    
    return historical


def compute_lambda_from_historical(historical_counts: List[int]) -> float:
    """
    Compute lambda (mean) parameter for Poisson distribution from historical counts.
    
    Handles edge cases:
    - Empty list: returns default 1.0
    - All zeros: returns minimum 0.1 (avoids degenerate distribution)
    - Negative values: filters them out
    
    Args:
        historical_counts: List of historical count integers
        
    Returns:
        Lambda parameter (mean) for Poisson distribution, with minimum of 0.1
    """
    if not historical_counts:
        return 1.0
    
    # Filter out negative values (shouldn't happen, but defensive)
    valid_counts = [c for c in historical_counts if c >= 0]
    if not valid_counts:
        return 1.0
    
    # Lambda is the mean of historical counts
    lambda_param = float(np.mean(valid_counts))
    
    # Enforce minimum lambda > 0 to avoid degenerate distributions
    # Use 0.1 as minimum to ensure valid Poisson distribution
    return max(lambda_param, 0.1)


async def run_forecast_for_camp(camp: Camp) -> List[ForecastResult]:
    """
    Run Poisson-based forecast for a camp.
    
    For each requirement in the camp:
    1. Try to fetch real historical counts from role_demand_history collection
    2. If no real data available, fall back to simulated historical counts
    3. Compute lambda (mean) from historical data
    4. Calculate Poisson percentiles (upper90, lower10)
    
    Args:
        camp: Camp object with requirements
        
    Returns:
        List of ForecastResult objects with role, slot, mean, upper90, lower10
    """
    results: List[ForecastResult] = []
    
    for req in camp.requirements:
        # Step 1: Try to fetch real historical counts from MongoDB
        historical_counts = await fetch_historical_counts_for_requirement(
            camp=camp,
            role=req.role,
            slot=req.slot
        )
        
        # Step 2: Fall back to simulation if no real data available
        if not historical_counts:
            # No real historical data found - use simulation as fallback
            historical_counts = simulate_historical_counts(req.count)
        
        # Step 3: Compute lambda from historical data (real or simulated)
        lambda_param = compute_lambda_from_historical(historical_counts)
        
        # Step 3: Calculate Poisson percentiles
        # Create Poisson distribution with computed lambda
        poisson_dist = stats.poisson(mu=lambda_param)
        
        # Calculate percentiles
        # upper90: 90th percentile (90% of the time, we'll need at most this many)
        # lower10: 10th percentile (10% of the time, we'll need at least this many)
        upper_90 = poisson_dist.ppf(0.90)
        lower_10 = poisson_dist.ppf(0.10)
        
        # Ensure lower_10 is at least 0 (Poisson is non-negative)
        lower_10 = max(0.0, lower_10)
        
        # Ensure upper_90 is at least the mean (should be, but safety check)
        upper_90 = max(lambda_param, upper_90)
        
        # Convert to integers for upper90 and lower10 as specified
        results.append(ForecastResult(
            slot=req.slot,
            role=req.role,
            mean=float(lambda_param),
            upper_90=float(int(upper_90)),  # Convert to int then float for GraphQL
            lower_10=float(int(lower_10))   # Convert to int then float for GraphQL
        ))
    
    return results
