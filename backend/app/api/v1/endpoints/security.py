from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from backend.app.schemas.common import APIResponse
from backend.app.schemas.security import (
    SecurityScanCreate,
    SecurityReportRead
)
from backend.app.services.security_service import security_service, ADVERSARIAL_VECTORS

router = APIRouter()

@router.get("/vectors", response_model=APIResponse[List[Dict[str, Any]]])
def list_attack_vectors():
    """Lists pre-packaged adversarial vectors used for vulnerability scanning."""
    safe_vectors = [
        {
            "category": v["category"],
            "attack_vector": v["attack_vector"],
            "risk_level": v["risk_level"],
            "prompt_preview": v["prompt"][:80] + "..."
        }
        for v in ADVERSARIAL_VECTORS
    ]
    return APIResponse(success=True, data=safe_vectors)

@router.post("/scan", response_model=APIResponse[SecurityReportRead])
async def execute_security_scan(payload: SecurityScanCreate):
    """
    Executes an adversarial safety evaluation against a target model.
    Evaluates Prompt Injection, Jailbreaks, PII Leakage, and Instruction Boundaries.
    """
    try:
        report = await security_service.scan_model(
            model_id=payload.model_id,
            categories=payload.categories,
            custom_prompts=payload.custom_attack_prompts
        )
        return APIResponse(
            success=True,
            message=f"Security scan completed for model '{payload.model_id}' (Defense rate: {report.defense_rate*100:.0f}%)",
            data=report
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Security scan failed: {e}")
