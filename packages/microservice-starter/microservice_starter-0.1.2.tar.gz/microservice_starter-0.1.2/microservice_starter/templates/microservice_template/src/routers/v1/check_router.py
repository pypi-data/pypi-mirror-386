from fastapi import APIRouter, HTTPException

CheckHealthRouter = APIRouter(prefix="/v1", tags=["Check"])


@CheckHealthRouter.get("/")
async def check():
    try:
        return {"Status": "V1 Checked"}
    except HTTPException as e:
        raise e
