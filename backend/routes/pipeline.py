from fastapi import APIRouter, HTTPException
from backend.pipeline.etl import main as run_etl  # ejecutamos el ETL directamente en Python

router = APIRouter(prefix="/api", tags=["Pipeline"])

@router.get("/pipeline/run")
def pipeline_run():
    try:
        run_etl()
        return {"ok": True, "message": "Pipeline executed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
