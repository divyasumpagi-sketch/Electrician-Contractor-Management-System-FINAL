from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from models import RoleEnum, RequestStatus

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: RoleEnum

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: RoleEnum
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class ElectricianOut(BaseModel):
    user_id: int
    approval_status: str
    specialization: Optional[str] = None
    rating: float

    # Nested user info
    user: UserOut

    class Config:
        from_attributes = True

class ServiceRequestCreate(BaseModel):
    category: str
    description: str

class ServiceRequestOut(BaseModel):
    id: int
    client_id: int
    category: str
    description: str
    status: RequestStatus
    created_at: datetime

    class Config:
        from_attributes = True

class StatusUpdate(BaseModel):
    status: RequestStatus

class PaymentOrder(BaseModel):
    request_id: int
    amount: float

class PaymentVerify(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    request_id: int
