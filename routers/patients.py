from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from datetime import date

import crud
import schemas
from database import get_db

router = APIRouter(prefix="/patients", tags=["patients"])

@router.get("", response_model=schemas.EnvelopeResponse[List[schemas.PatientResponse]])
async def list_patients(
    last_name: Optional[str] = None,
    date_of_birth: Optional[date] = None,
    phone_number: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    patients = await crud.get_patients(db, last_name, date_of_birth, phone_number)
    return {"data": patients, "error": None}

@router.get("/{id}", response_model=schemas.EnvelopeResponse[schemas.PatientResponse])
async def get_patient(id: UUID, db: AsyncSession = Depends(get_db)):
    patient = await crud.get_patient_by_id(db, id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"data": patient, "error": None}

@router.post("", status_code=status.HTTP_201_CREATED, response_model=schemas.EnvelopeResponse[schemas.PatientResponse])
async def create_patient(patient: schemas.PatientCreate, db: AsyncSession = Depends(get_db)):
    new_patient = await crud.create_patient(db, patient)
    return {"data": new_patient, "error": None}

@router.put("/{id}", response_model=schemas.EnvelopeResponse[schemas.PatientResponse])
async def update_patient(id: UUID, patient: schemas.PatientUpdate, db: AsyncSession = Depends(get_db)):
    updated_patient = await crud.update_patient(db, id, patient)
    if not updated_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"data": updated_patient, "error": None}

@router.delete("/{id}", response_model=schemas.EnvelopeResponse[schemas.PatientResponse])
async def delete_patient(id: UUID, db: AsyncSession = Depends(get_db)):
    deleted_patient = await crud.delete_patient(db, id)
    if not deleted_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"data": deleted_patient, "error": None}
