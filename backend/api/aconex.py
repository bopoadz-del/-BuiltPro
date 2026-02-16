from fastapi import APIRouter

router = APIRouter()


@router.get("/aconex/status")
def aconex_status():
    """
    Get Aconex API integration status.
    
    Returns:
        dict: Status information about the Aconex API integration
    """
    return {"status": "ok", "message": "Aconex API not wired yet"}