from fastapi import APIRouter
from digital_life.core import MemoryCardManager
from digital_life.models import MemoryCardsRequest, MemoryCard, MemoryCards, MemoryCardsGenerate, ChatHistoryOrText, MemoryCard2
from fastapi import FastAPI, HTTPException, status
import os

router = APIRouter(tags=["memory_card"])

MCmanager = MemoryCardManager(model_name="doubao-1-5-pro-32k-250115",
                              inference_save_case=True)

@router.post("/score")
async def score_from_memory_card_server(request: MemoryCardsRequest):
    """
    记忆卡片质量评分
    接收一个记忆卡片内容字符串，并返回其质量评分。
    """
    try:
        results = await MCmanager.ascore_from_memory_card(memory_cards=request.memory_cards)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MCmanager.ascore_from_memory_card Error : {e}",
        )
    return {"message": "memory card score successfully", "result": results}

@router.post("/merge", response_model=MemoryCard2, summary="记忆卡片合并")
async def memory_card_merge_server(request: MemoryCards) -> dict:
    try:
        memory_cards = request.model_dump()["memory_cards"]
        result = await MCmanager.amemory_card_merge(memory_cards=memory_cards)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MCmanager.amemory_card_merge Error : {e}",
        )
    return MemoryCard2(**result)

@router.post("/polish", response_model=MemoryCard, summary="记忆卡片发布AI润色")
async def memory_card_polish_server(request: MemoryCard) -> dict:
    """
    记忆卡片发布AI润色接口。
    接收记忆卡片内容，并返回AI润色后的结果。
    """
    try:
        memory_card = request.model_dump()
        result = await MCmanager.amemory_card_polish(memory_card=memory_card)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MCmanager.amemory_card_polish Error : {e}",
        )
    return MemoryCard(**result)


@router.post("/generate_by_text",response_model=MemoryCardsGenerate,summary="上传文件生成记忆卡片")
async def memory_card_generate_by_text_server(request: ChatHistoryOrText) -> dict:
    """
    # 0091 上传文件生成记忆卡片-memory_card_system_prompt
    # 0092 上传文件生成记忆卡片-time_prompt
    """
    try:
        chapters = await MCmanager.agenerate_memory_card_by_text(
            chat_history_str=request.text, weight=int(os.getenv("card_weight",1000))
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MCmanager.agenerate_memory_card_by_text Error : {e}",
        )
    return MemoryCardsGenerate(memory_cards=chapters)


@router.post("/generate",response_model=MemoryCardsGenerate,summary="聊天历史生成记忆卡片")
async def memory_card_generate_server(request: ChatHistoryOrText) -> dict:
    """
    # 0093 聊天历史生成记忆卡片-memory_card_system_prompt
    # 0094 聊天历史生成记忆卡片-time_prompt
    """
    try:
        chapters = await MCmanager.agenerate_memory_card(
            chat_history_str=request.text, weight=int(os.getenv("card_weight",1000))
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MCmanager.agenerate_memory_card Error : {e}",
        )
    return MemoryCardsGenerate(memory_cards=chapters)
    
