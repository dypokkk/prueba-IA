from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from app.tools.custom_tools import calculate_course_quote, check_level_placement

router = APIRouter(prefix="/api/tools", tags=["Custom Tools & Skills"])

class QuoteRequest(BaseModel):
    program_type: str = Field(default="standard_group", description="standard_group, intensive_group, saturday_intensive, private_10h, etc.")
    has_early_bird: bool = Field(default=False, description="Enrolling 10+ days in advance for 15% discount")
    has_sibling: bool = Field(default=False, description="Family discount 10%")
    annual_bundle: bool = Field(default=False, description="Annual bundle 25%")

class PlacementRequest(BaseModel):
    score_percentage: float = Field(..., ge=0.0, le=100.0, description="Score percentage (0.0 - 100.0)")

@router.post("/quote", response_model=Dict[str, Any])
async def compute_quote_tool(payload: QuoteRequest):
    """Custom Tool / Skill: Computes accurate tuition quotes, discounts, and installment breakdowns."""
    return calculate_course_quote(
        program_type=payload.program_type,
        has_early_bird=payload.has_early_bird,
        has_sibling=payload.has_sibling,
        annual_bundle=payload.annual_bundle
    )

@router.post("/placement", response_model=Dict[str, Any])
async def compute_placement_tool(payload: PlacementRequest):
    """Custom Tool / Skill: Evaluates diagnostic score and returns CEFR Level and recommended module."""
    return check_level_placement(score_percentage=payload.score_percentage)
