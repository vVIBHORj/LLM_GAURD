import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.db.models.dataset import Dataset, DatasetTestCase
from backend.app.schemas.common import APIResponse
from backend.app.schemas.dataset import DatasetCreate, DatasetRead, DatasetDetailRead, TestCaseCreate, TestCaseRead

router = APIRouter()

@router.get("", response_model=APIResponse[List[DatasetRead]])
def list_datasets(db: Session = Depends(get_db)):
    """Lists all datasets with their test case counts."""
    datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
    results = []
    for d in datasets:
        item = DatasetRead(
            id=d.id,
            name=d.name,
            description=d.description,
            task_type=d.task_type,
            version=d.version,
            created_at=d.created_at,
            test_case_count=len(d.test_cases)
        )
        results.append(item)

    return APIResponse(
        success=True,
        message=f"Found {len(results)} datasets",
        data=results
    )

@router.post("", response_model=APIResponse[DatasetDetailRead], status_code=201)
def create_dataset(payload: DatasetCreate, db: Session = Depends(get_db)):
    """Creates a new evaluation dataset, optionally with initial test cases."""
    dataset = Dataset(
        id=str(uuid.uuid4()),
        name=payload.name,
        description=payload.description,
        task_type=payload.task_type
    )
    db.add(dataset)
    db.flush()

    for tc in payload.test_cases:
        test_case = DatasetTestCase(
            id=str(uuid.uuid4()),
            dataset_id=dataset.id,
            prompt=tc.prompt,
            expected_output=tc.expected_output,
            context=tc.context,
            assertions=tc.assertions,
            metadata_payload=tc.metadata_payload
        )
        db.add(test_case)

    db.commit()
    db.refresh(dataset)

    tc_reads = [TestCaseRead.model_validate(tc) for tc in dataset.test_cases]
    detail = DatasetDetailRead(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        task_type=dataset.task_type,
        version=dataset.version,
        created_at=dataset.created_at,
        test_case_count=len(tc_reads),
        test_cases=tc_reads
    )

    return APIResponse(
        success=True,
        message=f"Dataset '{dataset.name}' created with {len(tc_reads)} test cases",
        data=detail
    )

@router.get("/{dataset_id}", response_model=APIResponse[DatasetDetailRead])
def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Retrieves dataset details along with all test cases."""
    dataset = db.query(Dataset).filter_by(id=dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    tc_reads = [TestCaseRead.model_validate(tc) for tc in dataset.test_cases]
    detail = DatasetDetailRead(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        task_type=dataset.task_type,
        version=dataset.version,
        created_at=dataset.created_at,
        test_case_count=len(tc_reads),
        test_cases=tc_reads
    )

    return APIResponse(success=True, data=detail)

@router.post("/{dataset_id}/test-cases", response_model=APIResponse[TestCaseRead], status_code=201)
def add_test_case(dataset_id: str, payload: TestCaseCreate, db: Session = Depends(get_db)):
    """Appends a new test case to an existing dataset."""
    dataset = db.query(Dataset).filter_by(id=dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    tc = DatasetTestCase(
        id=str(uuid.uuid4()),
        dataset_id=dataset.id,
        prompt=payload.prompt,
        expected_output=payload.expected_output,
        context=payload.context,
        assertions=payload.assertions,
        metadata_payload=payload.metadata_payload
    )
    db.add(tc)
    db.commit()
    db.refresh(tc)

    return APIResponse(
        success=True,
        message="Test case added successfully",
        data=TestCaseRead.model_validate(tc)
    )
