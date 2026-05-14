from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, DateTime, Float, Text
from sqlalchemy.orm import relationship
from database import Base
import enum
from datetime import datetime

class RoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    CLIENT = "CLIENT"
    ELECTRICIAN = "ELECTRICIAN"

class RequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("ElectricianProfile", back_populates="user", uselist=False)

class ElectricianProfile(Base):
    __tablename__ = "electrician_profiles"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    approval_status = Column(String(20), default="PENDING") # PENDING, APPROVED, REJECTED
    specialization = Column(String(255))
    rating = Column(Float, default=0.0)

    user = relationship("User", back_populates="profile")

class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("users.id"))
    category = Column(String(100))
    description = Column(Text)
    image_url = Column(String(255), nullable=True)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("service_requests.id"))
    amount = Column(Float)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    razorpay_order_id = Column(String(255), nullable=True)
    razorpay_payment_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
