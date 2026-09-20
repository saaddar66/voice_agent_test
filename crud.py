from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from datetime import date, datetime, timezone
from typing import Optional

import models
import schemas

async def get_patients(
    db: AsyncSession, 
    last_name: Optional[str] = None, 
    date_of_birth: Optional[date] = None, 
    phone_number: Optional[str] = None
):
    query = select(models.Patient).where(models.Patient.deleted_at.is_(None))
    
    if last_name:
        query = query.where(models.Patient.last_name == last_name)
    if date_of_birth:
        query = query.where(models.Patient.date_of_birth == date_of_birth)
    if phone_number:
        query = query.where(models.Patient.phone_number == phone_number)
        
    result = await db.execute(query)
    return result.scalars().all()

async def get_patient_by_id(db: AsyncSession, patient_id: UUID):
    query = select(models.Patient).where(
        models.Patient.patient_id == patient_id,
        models.Patient.deleted_at.is_(None)
    )
    result = await db.execute(query)
    return result.scalars().first()

async def create_patient(db: AsyncSession, patient: schemas.PatientCreate):
    db_patient = models.Patient(**patient.model_dump())
    db.add(db_patient)
    await db.commit()
    await db.refresh(db_patient)
    return db_patient

async def update_patient(db: AsyncSession, patient_id: UUID, patient: schemas.PatientUpdate):
    db_patient = await get_patient_by_id(db, patient_id)
    if not db_patient:
        return None
        
    update_data = patient.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_patient, key, value)
        
    await db.commit()
    await db.refresh(db_patient)
    return db_patient

async def delete_patient(db: AsyncSession, patient_id: UUID):
    db_patient = await get_patient_by_id(db, patient_id)
    if not db_patient:
        return None
        
    db_patient.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(db_patient)
    return db_patient
