
from fastapi import APIRouter
from digital_life.core import DigitalAvatar
from digital_life.models import BriefResponse, MemoryCards, AvatarXGRequests
from fastapi import FastAPI, HTTPException, status
router = APIRouter(tags=["digital_avatar"])
da = DigitalAvatar(inference_save_case = False,
                   model_name = "doubao-1-5-pro-32k-250115")

@router.post(
    "/brief", response_model=BriefResponse, description="数字分身介绍"
)
async def brief_server(request: MemoryCards):
    try:
        memory_cards = request.model_dump()["memory_cards"]
        result = await da.abrief(memory_cards=memory_cards)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DigitalAvatar.abrief Error : {e}",
        )
    return BriefResponse(
        title=result.get("title"),
        content=result.get("content"),
        tags=result.get("tags")[:2],
    )


@router.post("/personality_extraction")
async def digital_avatar_personality_extraction(request: AvatarXGRequests):
    """数字分身性格提取"""
    try:
        memory_cards = request.model_dump()["memory_cards"]
        result = await da.personality_extraction(memory_cards=memory_cards,action = request.action,old_character = request.old_character)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DigitalAvatar.personality_extraction Error : {e}",
        )
    return {"text": result}


@router.post("/desensitization")
async def digital_avatar_desensitization(request: MemoryCards):
    """
    数字分身脱敏
    """
    try:
        memory_cards = request.model_dump()["memory_cards"]
        result = await da.desensitization(memory_cards=memory_cards)
        memory_cards = {"memory_cards": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DigitalAvatar.desensitization Error : {e}",
        )
    return MemoryCards(**memory_cards)
