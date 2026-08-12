from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from schema.swapRequest import SwapRequestCreate, SwapRequestResponse, SwapRequestUpdate
from models.swapRequest import SwapRequest
from database import get_db
from utility import get_current_user

swap_router = APIRouter(prefix="/swap-requests", tags=["swap-requests"])

@swap_router.post("/", status_code=201, response_model=SwapRequestResponse)
async def create_swap_request(swap: SwapRequestCreate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    sender_id = current_user.get("sub")
    new_swap = SwapRequest(
        sender_id=sender_id,
        receiver_id=swap.receiver_id,
        status="pending",
        skill_offered=swap.skill_offered,
        skill_requested=swap.skill_requested
    )
    db.add(new_swap)
    await db.commit()
    await db.refresh(new_swap)
    return new_swap

@swap_router.get("/incoming/{user_id}", response_model=list[SwapRequestResponse])
async def get_incoming_requests(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SwapRequest).where(SwapRequest.receiver_id == user_id)
    )
    requests = result.scalars().all()
    return requests

@swap_router.get("/outgoing/{user_id}", response_model=list[SwapRequestResponse])
async def get_outgoing_requests(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SwapRequest).where(SwapRequest.sender_id == user_id)
    )
    requests = result.scalars().all()
    return requests

@swap_router.patch("/{request_id}", response_model=SwapRequestResponse)
async def update_swap_request(request_id: str, update: SwapRequestUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SwapRequest).where(SwapRequest.id == request_id))
    swap = result.scalar_one_or_none()
    
    if not swap:
        raise HTTPException(status_code=404, detail="Swap request not found")
    
    swap.status = update.status
    await db.commit()
    await db.refresh(swap)
    return swap
