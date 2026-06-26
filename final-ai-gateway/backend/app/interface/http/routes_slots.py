"""
Slots Routes — GET /api/v1/slots
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request

from app.domain.ports.slot_repository import SlotRepositoryPort

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/slots", tags=["slots"])


def get_slot_repo(request: Request) -> SlotRepositoryPort:
    return request.app.state.slot_repo


@router.get("")
async def list_slots(
    slot_repo: SlotRepositoryPort = Depends(get_slot_repo),
):
    """List all model backend slots and their status."""
    slots = await slot_repo.get_all_slots()
    return {
        "total_slots": len(slots),
        "slots": [
            {
                "slot_id": s.slot_id,
                "status": s.status.value,
                "current_request_id": s.current_request_id,
                "prompt_tokens": s.prompt_tokens,
                "tokens_generated": s.tokens_generated,
            }
            for s in slots
        ],
    }
