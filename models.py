import enum
import uuid
from sqlalchemy import Column, String, Date, DateTime, Enum, func
from sqlalchemy.dialects.postgresql import UUID
from database import Base

class SexEnum(str, enum.Enum):
    male = "Male"
    female = "Female"
    other = "Other"
    decline = "Decline to Answer"

class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    sex = Column(Enum(SexEnum, name="sex_enum"), nullable=False)
    phone_number = Column(String(10), nullable=False)
    email = Column(String, nullable=True)
    
    address_line_1 = Column(String, nullable=False)
    address_line_2 = Column(String, nullable=True)
    city = Column(String, nullable=False)
    state = Column(String(2), nullable=False)
    zip_code = Column(String(5), nullable=False)
    
    insurance_provider = Column(String, nullable=True)
    insurance_member_id = Column(String, nullable=True)
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    
    preferred_language = Column(String, default="English", nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
