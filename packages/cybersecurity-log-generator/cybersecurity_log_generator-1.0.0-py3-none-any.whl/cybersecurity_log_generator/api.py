"""
FastAPI application for cybersecurity log generation.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json

from .core.generator import LogGenerator
from .core.enhanced_generator import EnhancedLogGenerator
from .core.models import LogType, CyberdefensePillar
from .config import config


# FastAPI app
app = FastAPI(
    title="Cybersecurity Log Generator API",
    description="Generate synthetic cybersecurity logs for testing and analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize generators
basic_generator = LogGenerator()
enhanced_generator = EnhancedLogGenerator()


class LogGenerationRequest(BaseModel):
    log_type: str
    count: int = 100
    time_range: str = "24h"


class PillarLogGenerationRequest(BaseModel):
    pillar: str
    count: int = 100
    time_range: str = "24h"


class LogGenerationResponse(BaseModel):
    success: bool
    count: int
    logs: List[Dict[str, Any]]
    message: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Cybersecurity Log Generator API",
        "version": "1.0.0",
        "endpoints": {
            "generate": "/generate",
            "pillar": "/pillar",
            "types": "/types",
            "pillars": "/pillars",
            "docs": "/docs"
        }
    }


@app.post("/generate", response_model=LogGenerationResponse)
async def generate_logs(request: LogGenerationRequest):
    """Generate basic cybersecurity logs."""
    try:
        log_type = LogType(request.log_type.lower())
        logs = basic_generator.generate_logs(
            log_type=log_type,
            count=request.count,
            time_range=request.time_range
        )
        
        # Convert to dictionary format
        logs_data = [log.dict() if hasattr(log, 'dict') else log for log in logs]
        
        return LogGenerationResponse(
            success=True,
            count=len(logs_data),
            logs=logs_data,
            message=f"Generated {len(logs_data)} {request.log_type} logs"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating logs: {str(e)}")


@app.post("/pillar", response_model=LogGenerationResponse)
async def generate_pillar_logs(request: PillarLogGenerationRequest):
    """Generate logs for specific cyberdefense pillars."""
    try:
        pillar = CyberdefensePillar(request.pillar.lower())
        logs = enhanced_generator.generate_logs(
            pillar=pillar,
            count=request.count,
            time_range=request.time_range
        )
        
        # Convert to dictionary format
        logs_data = [log.dict() if hasattr(log, 'dict') else log for log in logs]
        
        return LogGenerationResponse(
            success=True,
            count=len(logs_data),
            logs=logs_data,
            message=f"Generated {len(logs_data)} {request.pillar} logs"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating pillar logs: {str(e)}")


@app.get("/types")
async def get_supported_types():
    """Get all supported log types."""
    return {
        "log_types": [log_type.value for log_type in LogType],
        "count": len(LogType)
    }


@app.get("/pillars")
async def get_supported_pillars():
    """Get all supported cyberdefense pillars."""
    return {
        "pillars": [pillar.value for pillar in CyberdefensePillar],
        "count": len(CyberdefensePillar)
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "cybersecurity-log-generator"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.api_host, port=config.api_port)
