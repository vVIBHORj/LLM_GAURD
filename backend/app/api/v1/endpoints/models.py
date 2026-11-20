from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.db.models.model import Model
from backend.app.schemas.common import APIResponse
from backend.app.schemas.model import ModelRead, ModelSyncResponse
from backend.app.services.ollama_service import ollama_service

router = APIRouter()

@router.get("", response_model=APIResponse[List[ModelRead]])
def list_registered_models(db: Session = Depends(get_db)):
    """Lists all models registered in the LocalLLM Guard database."""
    models = db.query(Model).order_by(Model.name.asc()).all()
    return APIResponse(
        success=True,
        message=f"Found {len(models)} registered models",
        data=[ModelRead.model_validate(m) for m in models]
    )

@router.post("/sync", response_model=APIResponse[ModelSyncResponse])
async def sync_models_from_ollama(db: Session = Depends(get_db)):
    """
    Queries local Ollama tags API and synchronizes discovered models into the database.
    """
    try:
        discovered = await ollama_service.list_models()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Ollama is unreachable: {e}")

    now = datetime.utcnow()
    synced_models: List[Model] = []

    for item in discovered:
        m_id = item.get("name")
        if not m_id:
            continue

        details = item.get("details", {})
        family = details.get("family")
        parameter_size = details.get("parameter_size")
        quantization = details.get("quantization_level")
        disk_size = item.get("size")

        existing: Model | None = db.query(Model).filter(Model.id == m_id).first()
        if existing:
            existing.name = m_id
            existing.family = family
            existing.parameter_size = parameter_size
            existing.quantization = quantization
            existing.disk_size_bytes = disk_size
            existing.is_available = True
            existing.last_seen_at = now
            synced_models.append(existing)
        else:
            new_model = Model(
                id=m_id,
                name=m_id,
                family=family,
                parameter_size=parameter_size,
                quantization=quantization,
                disk_size_bytes=disk_size,
                is_available=True,
                last_seen_at=now
            )
            db.add(new_model)
            synced_models.append(new_model)

    db.commit()
    for m in synced_models:
        db.refresh(m)

    sync_payload = ModelSyncResponse(
        discovered_count=len(synced_models),
        models=[ModelRead.model_validate(m) for m in synced_models]
    )

    return APIResponse(
        success=True,
        message=f"Successfully synced {len(synced_models)} models from Ollama",
        data=sync_payload
    )
