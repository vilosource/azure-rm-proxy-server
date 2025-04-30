from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def get_project_info():
    """
    Simple endpoint to return the project name and version.
    """
    return {"project_name": "Azure RM Proxy Server", "version": "1.0.0"}
