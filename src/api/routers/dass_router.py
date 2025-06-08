from fastapi import APIRouter, Depends, HTTPException

from src.services.inference import predict_dass
from src.models.user_models import UserPublic
from src.models.api_models import DASS21Payload, Recommendation
from src.core.security import get_current_user
from src.clients.satusehat_client import get_all_locations_by_org
from src.core.config import settings

router = APIRouter()

@router.post(
    "/dass21",
    response_model=Recommendation,
    summary="Proses DASS-21 dan rekomendasi",
    tags=["dass21"]
)
async def process_dass(payload: DASS21Payload, current_user: UserPublic = Depends(get_current_user)):
    try:
        # Use the authenticated user's email as the identifier.
        user_identifier = current_user.email 

        result = predict_dass(
            payload.depression,
            payload.anxiety,
            payload.stress
        )

        response = {
            "level": result["level"],
            "message": result["message"],
            "advice": result.get("advice", ""),
        }

        if result["level"] in {"severe", "extremely"}:
            org_id = settings.ORGANIZATION_ID
            satusehat_faskes = await get_all_locations_by_org(org_id)
  
            response["available_facilities"] = [
                {
                    "id": org["resource"]["id"],
                    "name": org["resource"]["name"],
                } for org in satusehat_faskes
            ]

        return response

    except Exception as e:
        import traceback
        print(f"ERROR in /api/dass21 endpoint for user {current_user.email}:")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        print("Full traceback:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error while processing DASS21. Details: {str(e)}") 