"""Local API service for ElevenLabs webhook/tool integration.

Run behind Cloudflare Tunnel. The service itself should bind to localhost.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from availability_search import compact_options, search_availability  # noqa: E402
from db import connect_to_db  # noqa: E402


API_CONFIG_PATH = PROJECT_ROOT / "config" / "api.local.json"
API_CONFIG_EXAMPLE_PATH = PROJECT_ROOT / "config" / "api.local.example.json"


def load_api_config() -> dict[str, Any]:
    if API_CONFIG_PATH.exists():
        with API_CONFIG_PATH.open("r", encoding="utf-8") as config_file:
            return json.load(config_file)
    if API_CONFIG_EXAMPLE_PATH.exists():
        with API_CONFIG_EXAMPLE_PATH.open("r", encoding="utf-8") as config_file:
            return json.load(config_file)
    return {}


API_CONFIG = load_api_config()
API_TOKEN = os.getenv("MEDICUS_API_TOKEN") or API_CONFIG.get("bearer_token")


class AvailabilityRequest(BaseModel):
    service: str = "skin"
    date_from: str | None = None
    date_to: str | None = None
    days_ahead: int | None = None
    include_weekends: bool = False
    weekdays: list[int] = Field(default_factory=list)
    time_from: str | None = None
    time_to: str | None = None
    doctor_id: int | None = None
    doctor_name: str | None = None
    limit: int | None = None
    compact: bool = False


class PlaceholderRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)


def require_auth(authorization: str | None = Header(default=None)) -> None:
    if not API_TOKEN or API_TOKEN == "CHANGE_ME":
        return
    expected = f"Bearer {API_TOKEN}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="invalid Authorization bearer token")


app = FastAPI(title="Medicus Local API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "service": "medicus-local-api"}


@app.post("/doctor-availability", dependencies=[Depends(require_auth)])
def doctor_availability(request: AvailabilityRequest | None = None) -> dict[str, Any]:
    connection = None
    try:
        payload = request.dict(exclude_none=True) if request is not None else {}
        payload.setdefault("days_ahead", API_CONFIG.get("default_days_ahead", 30))
        payload.setdefault("limit", API_CONFIG.get("default_limit", 3))
        payload.setdefault("max_limit", API_CONFIG.get("max_limit", 10))

        connection = connect_to_db()
        cursor = connection.cursor()
        response = search_availability(cursor, payload)
        if payload.get("compact"):
            return compact_options(response)
        return response
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"doctor availability failed: {error}") from error
    finally:
        if connection is not None:
            connection.close()


@app.post("/patient-lookup", dependencies=[Depends(require_auth)])
def patient_lookup(_request: PlaceholderRequest | None = None) -> dict[str, Any]:
    return {
        "ok": False,
        "status": "not_implemented",
        "message": "Patient lookup endpoint is reserved for the next integration phase.",
    }


@app.post("/book-appointment", dependencies=[Depends(require_auth)])
def book_appointment(_request: PlaceholderRequest | None = None) -> dict[str, Any]:
    return {
        "ok": False,
        "status": "not_implemented",
        "message": "Booking endpoint is reserved for the next integration phase and performs no database writes.",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api_server:app",
        host=str(API_CONFIG.get("host", "127.0.0.1")),
        port=int(API_CONFIG.get("port", 8000)),
        reload=False,
    )
