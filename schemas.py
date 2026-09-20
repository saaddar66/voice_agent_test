from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import date, datetime
from typing import Optional, TypeVar, Generic
from uuid import UUID
import re
from models import SexEnum

T = TypeVar('T')

class EnvelopeResponse(BaseModel, Generic[T]):
    data: Optional[T] = None
    error: Optional[str] = None

class PatientBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: date
    sex: SexEnum
    phone_number: str
    email: Optional[str] = None
    
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str = Field(..., min_length=2, max_length=2)
    zip_code: str = Field(..., min_length=5, max_length=5)
    
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    
    preferred_language: str = "English"

    @field_validator('sex', mode='before')
    @classmethod
    def parse_sex_leniently(cls, v):
        if isinstance(v, str):
            v_lower = v.lower().strip()
            if v_lower == 'male': return 'Male'
            if v_lower == 'female': return 'Female'
            if v_lower == 'other': return 'Other'
            if 'decline' in v_lower: return 'Decline to Answer'
        return v

    @field_validator('date_of_birth')
    @classmethod
    def dob_must_not_be_in_future(cls, v: date):
        if v > date.today():
            raise ValueError('date_of_birth cannot be in the future')
        return v

    @field_validator('phone_number')
    @classmethod
    def phone_number_must_be_10_digits(cls, v: str):
        if not re.match(r'^\d{10}$', v):
            raise ValueError('phone_number must contain exactly 10 digits')
        return v
    
    @field_validator('emergency_contact_phone')
    @classmethod
    def emerg_phone_number_must_be_10_digits(cls, v: Optional[str]):
        if v is not None and not re.match(r'^\d{10}$', v):
            raise ValueError('emergency_contact_phone must contain exactly 10 digits')
        return v

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    date_of_birth: Optional[date] = None
    sex: Optional[SexEnum] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = Field(None, min_length=2, max_length=2)
    zip_code: Optional[str] = Field(None, min_length=5, max_length=5)
    
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    
    preferred_language: Optional[str] = None

    @field_validator('sex', mode='before')
    @classmethod
    def parse_sex_leniently(cls, v):
        if isinstance(v, str):
            v_lower = v.lower().strip()
            if v_lower == 'male': return 'Male'
            if v_lower == 'female': return 'Female'
            if v_lower == 'other': return 'Other'
            if 'decline' in v_lower: return 'Decline to Answer'
        return v

    @field_validator('date_of_birth')
    @classmethod
    def dob_must_not_be_in_future(cls, v: Optional[date]):
        if v and v > date.today():
            raise ValueError('date_of_birth cannot be in the future')
        return v

    @field_validator('phone_number')
    @classmethod
    def phone_number_must_be_10_digits(cls, v: Optional[str]):
        if v is not None and not re.match(r'^\d{10}$', v):
            raise ValueError('phone_number must contain exactly 10 digits')
        return v
    
    @field_validator('emergency_contact_phone')
    @classmethod
    def emerg_phone_number_must_be_10_digits(cls, v: Optional[str]):
        if v is not None and not re.match(r'^\d{10}$', v):
            raise ValueError('emergency_contact_phone must contain exactly 10 digits')
        return v

class PatientResponse(PatientBase):
    patient_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
