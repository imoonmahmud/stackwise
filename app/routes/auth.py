from datetime import timedelta
from decimal import Decimal
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.database import get_db
from app.models.user import User
from app.schemas.tool import ToolList
from app.schemas.user import Token, UserCreate, UserRead
from app.services.tool_service import get_tools
from app.services.user_service import authenticate_user, register_user
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Annotated[Session, Depends(get_db)]):
    return register_user(db, user_in)

@router.post("/login", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)]
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(user.id)
    return Token(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=UserRead)
def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.get("/me/saved-tools", response_model=ToolList)
def get_my_saved_tools(
    search: str | None = None,
    free_plan: bool | None = None,
    api_available: bool | None = None,
    pricing_model: str | None = None,
    category: str | None = None,
    feature: list[str] | None = Query(default=None),
    limit: int = 20,
    offset: int = 0,
    sort: Literal['name', '-name', 'newest'] = 'name',
    max_price: Decimal | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_tools(
        db=db,
        search=search,
        free_plan=free_plan,
        api_available=api_available,
        pricing_model=pricing_model,
        category=category,
        feature=feature,
        limit=limit,
        offset=offset,
        sort=sort,
        max_price=max_price,
        saved_by_user_id=current_user.id
    )