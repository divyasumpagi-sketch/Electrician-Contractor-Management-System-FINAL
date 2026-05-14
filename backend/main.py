from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

import models
import schemas
import auth
import database
import razorpay
import os
from database import engine

# Razorpay Client Setup
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Create database tables
models.Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(title="AxiLex Electrician Management API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# Home Route
# ─────────────────────────────────────────────────────────────
@app.get("/")
def home():
    return {"message": "AxiLex Backend Running Successfully"}


# ─────────────────────────────────────────────────────────────
# Auth: Register
# ─────────────────────────────────────────────────────────────
@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create electrician profile if role is electrician
    if user.role == models.RoleEnum.ELECTRICIAN:
        profile = models.ElectricianProfile(user_id=new_user.id)
        db.add(profile)
        db.commit()

    return new_user


# ─────────────────────────────────────────────────────────────
# Auth: Login
# ─────────────────────────────────────────────────────────────
@app.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db)
):
    print(f"Login attempt for: {form_data.username}")
    user = db.query(models.User).filter(models.User.email == form_data.username).first()

    if not user:
        print("User NOT found in database")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    print(f"User found: {user.email}, verifying password...")
    if not auth.verify_password(form_data.password, user.hashed_password):
        print("Password verification FAILED")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print("Login SUCCESSFUL")

    access_token = auth.create_access_token(
        data={"sub": user.email, "role": user.role.value},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


# ─────────────────────────────────────────────────────────────
# Current Logged In User
# ─────────────────────────────────────────────────────────────
@app.get("/users/me", response_model=schemas.UserOut)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


# ─────────────────────────────────────────────────────────────
# Admin: List All Users
# ─────────────────────────────────────────────────────────────
@app.get("/admin/users", response_model=List[schemas.UserOut])
def get_all_users(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != models.RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return db.query(models.User).all()


# ─────────────────────────────────────────────────────────────
# Admin: List Electricians with approval status
# ─────────────────────────────────────────────────────────────
@app.get("/admin/electricians", response_model=List[schemas.ElectricianOut])
def get_electricians(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != models.RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return db.query(models.ElectricianProfile).join(models.User).all()


# ─────────────────────────────────────────────────────────────
# Admin: Approve / Reject Electrician
# ─────────────────────────────────────────────────────────────
@app.patch("/admin/electricians/{user_id}/approve")
def approve_electrician(
    user_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != models.RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    profile = db.query(models.ElectricianProfile).filter(models.ElectricianProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Electrician not found")
    profile.approval_status = "APPROVED"
    db.commit()
    return {"message": "Electrician approved"}

@app.patch("/admin/electricians/{user_id}/reject")
def reject_electrician(
    user_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != models.RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    profile = db.query(models.ElectricianProfile).filter(models.ElectricianProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Electrician not found")
    profile.approval_status = "REJECTED"
    db.commit()
    return {"message": "Electrician rejected"}


# ─────────────────────────────────────────────────────────────
# Admin: Stats
# ─────────────────────────────────────────────────────────────
@app.get("/admin/stats")
def get_stats(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != models.RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    total_users = db.query(models.User).count()
    pending_requests = db.query(models.ServiceRequest).filter(
        models.ServiceRequest.status == models.RequestStatus.PENDING
    ).count()
    completed_jobs = db.query(models.ServiceRequest).filter(
        models.ServiceRequest.status == models.RequestStatus.COMPLETED
    ).count()
    return {
        "total_users": total_users,
        "pending_requests": pending_requests,
        "completed_jobs": completed_jobs
    }


# ─────────────────────────────────────────────────────────────
# Client: Create Service Request
# ─────────────────────────────────────────────────────────────
@app.post("/requests", response_model=schemas.ServiceRequestOut)
def create_request(
    req: schemas.ServiceRequestCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != models.RoleEnum.CLIENT:
        raise HTTPException(status_code=403, detail="Client access required")
    new_req = models.ServiceRequest(
        client_id=current_user.id,
        category=req.category,
        description=req.description
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)
    return new_req


# ─────────────────────────────────────────────────────────────
# Client: Get My Requests
# ─────────────────────────────────────────────────────────────
@app.get("/requests/my", response_model=List[schemas.ServiceRequestOut])
def get_my_requests(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != models.RoleEnum.CLIENT:
        raise HTTPException(status_code=403, detail="Client access required")
    return db.query(models.ServiceRequest).filter(
        models.ServiceRequest.client_id == current_user.id
    ).order_by(models.ServiceRequest.created_at.desc()).all()


# ─────────────────────────────────────────────────────────────
# Electrician: Get Assigned Jobs (all PENDING/ASSIGNED requests)
# ─────────────────────────────────────────────────────────────
@app.get("/jobs", response_model=List[schemas.ServiceRequestOut])
def get_jobs(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != models.RoleEnum.ELECTRICIAN:
        raise HTTPException(status_code=403, detail="Electrician access required")
    return db.query(models.ServiceRequest).filter(
        models.ServiceRequest.status.in_([
            models.RequestStatus.PENDING,
            models.RequestStatus.ASSIGNED,
            models.RequestStatus.IN_PROGRESS
        ])
    ).order_by(models.ServiceRequest.created_at.desc()).all()


# ─────────────────────────────────────────────────────────────
# Electrician: Update Job Status
# ─────────────────────────────────────────────────────────────
@app.patch("/jobs/{request_id}/status")
def update_job_status(
    request_id: int,
    status_update: schemas.StatusUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != models.RoleEnum.ELECTRICIAN:
        raise HTTPException(status_code=403, detail="Electrician access required")
    req = db.query(models.ServiceRequest).filter(models.ServiceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    req.status = status_update.status
    db.commit()
    return {"message": f"Status updated to {status_update.status}"}
# ─────────────────────────────────────────────────────────────
# Payment: Create Razorpay Order
# ─────────────────────────────────────────────────────────────
@app.post("/payments/create-order")
def create_payment_order(
    order_data: schemas.PaymentOrder,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != models.RoleEnum.CLIENT:
        raise HTTPException(status_code=403, detail="Client access required")
    
    # Create Razorpay Order
    data = {
        "amount": int(order_data.amount * 100), # amount in paise
        "currency": "INR",
        "receipt": f"receipt_{order_data.request_id}",
        "payment_capture": 1
    }
    
    try:
        razor_order = razorpay_client.order.create(data=data)
        
        # Save payment record
        new_payment = models.Payment(
            request_id=order_data.request_id,
            amount=order_data.amount,
            status=models.PaymentStatus.PENDING,
            razorpay_order_id=razor_order['id']
        )
        db.add(new_payment)
        db.commit()
        
        return razor_order
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────────────────────
# Payment: Verify Signature
# ─────────────────────────────────────────────────────────────
@app.post("/payments/verify")
def verify_payment(
    verify_data: schemas.PaymentVerify,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    # Verify signature
    params_dict = {
        'razorpay_order_id': verify_data.razorpay_order_id,
        'razorpay_payment_id': verify_data.razorpay_payment_id,
        'razorpay_signature': verify_data.razorpay_signature
    }
    
    try:
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # Update payment status
        payment = db.query(models.Payment).filter(
            models.Payment.razorpay_order_id == verify_data.razorpay_order_id
        ).first()
        
        if payment:
            payment.status = models.PaymentStatus.SUCCESS
            payment.razorpay_payment_id = verify_data.razorpay_payment_id
            
            # Update request status to COMPLETED if it was IN_PROGRESS
            service_req = db.query(models.ServiceRequest).filter(
                models.ServiceRequest.id == verify_data.request_id
            ).first()
            if service_req:
                service_req.status = models.RequestStatus.COMPLETED
            
            db.commit()
            return {"status": "Payment Successful"}
        
        raise HTTPException(status_code=404, detail="Payment record not found")
        
    except Exception as e:
        # Update payment status to FAILED
        payment = db.query(models.Payment).filter(
            models.Payment.razorpay_order_id == verify_data.razorpay_order_id
        ).first()
        if payment:
            payment.status = models.PaymentStatus.FAILED
            db.commit()
        
        raise HTTPException(status_code=400, detail="Payment verification failed")