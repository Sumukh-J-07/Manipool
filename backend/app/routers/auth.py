import random
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import (
    DemoLoginRequest,
    LoginRequest,
    OTPRequest,
    OTPVerifyRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserProfile,
)
from backend.app.services.auth_service import (
    create_access_token,
    get_current_user,
    hash_password,
    is_eligible_student_email,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if not is_eligible_student_email(req.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration restricted to MAHE student domains: {', '.join(settings.ALLOWED_DOMAINS)}",
        )

    # Check existing user
    stmt = select(User).where(User.email == req.email.lower().strip())
    res = await db.execute(stmt)
    existing = res.scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    pwd_hash = hash_password(req.password) if req.password else None
    new_user = User(
        name=req.name.strip(),
        email=req.email.lower().strip(),
        area=req.area.strip(),
        password_hash=pwd_hash,
        is_verified=True,  # initial registration verified in demo/pilot
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    token = create_access_token({"sub": new_user.id, "email": new_user.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserProfile.model_validate(new_user),
    )


@router.post("/request-otp")
async def request_otp(req: OTPRequest, db: AsyncSession = Depends(get_db)):
    email_clean = req.email.lower().strip()
    if not is_eligible_student_email(email_clean):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only MAHE institutional email addresses are permitted.",
        )

    stmt = select(User).where(User.email == email_clean)
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user:
        user = User(
            email=email_clean,
            name=email_clean.split("@")[0].capitalize(),
            area="MAHE Campus",
            is_verified=False,
        )
        db.add(user)

    # Generate 6-digit OTP
    otp_code = f"{random.randint(100000, 999999)}"
    user.otp_code = otp_code
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
    await db.commit()

    response = {
        "message": f"Verification code sent to {email_clean}",
        "expires_in_minutes": 10,
    }
    # In dev/test mode or pilot, include the OTP for automated testing and demo flow
    if settings.DEV_MODE:
        response["dev_otp_code"] = otp_code

    return response


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(req: OTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    email_clean = req.email.lower().strip()
    stmt = select(User).where(User.email == email_clean)
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user or not user.otp_code or not user.otp_expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active OTP request found for this email.",
        )

    if datetime.utcnow() > user.otp_expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new one.",
        )

    if user.otp_code != req.code.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code.",
        )

    user.is_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserProfile.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    email_clean = req.email.lower().strip()
    stmt = select(User).where(User.email == email_clean)
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user or not user.password_hash or not verify_password(user.password_hash, req.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    token = create_access_token({"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserProfile.model_validate(user),
    )


@router.post("/demo-login", response_model=TokenResponse)
async def demo_login(req: DemoLoginRequest, db: AsyncSession = Depends(get_db)):
    email_clean = req.email.lower().strip()
    if not is_eligible_student_email(email_clean):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Demo login requires a MAHE email address (@learner.manipal.edu).",
        )

    stmt = select(User).where(User.email == email_clean)
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user:
        name = req.name.strip() if req.name else email_clean.split("@")[0].capitalize()
        user = User(
            email=email_clean,
            name=name,
            area=req.area or "MAHE Campus",
            is_verified=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_access_token({"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserProfile.model_validate(user),
    )


@router.get("/me", response_model=UserProfile)
async def get_me(user: User = Depends(get_current_user)):
    return UserProfile.model_validate(user)


@router.put("/profile", response_model=UserProfile)
async def update_profile(
    req: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if req.name is not None and req.name.strip():
        user.name = req.name.strip()
    if req.area is not None and req.area.strip():
        user.area = req.area.strip()
    await db.commit()
    await db.refresh(user)
    return UserProfile.model_validate(user)
