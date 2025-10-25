# (C) Copyright 2024- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

"""FastAPI Entrypoint"""

import logging
import os
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from forecastbox.db.job import create_db_and_tables as create_job_db
from forecastbox.db.migrations import migrate
from forecastbox.db.model import create_db_and_tables as create_model_db
from forecastbox.db.user import create_db_and_tables as create_user_db
from starlette.exceptions import HTTPException

from .api.routers import admin, auth, execution, gateway, job, model, product
from .config import config

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.debug("Starting FIAB with config: %s", config)
    await create_user_db()
    await create_job_db()
    await create_model_db()
    migrate()
    yield
    await gateway.shutdown_processes()


app = FastAPI(
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
    title="Forecast in a Box API",
    version="1.0.0",
    lifespan=lifespan,
)

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


app.include_router(model.router, prefix="/api/v1/model")
app.include_router(product.router, prefix="/api/v1/product")
app.include_router(execution.router, prefix="/api/v1/execution")
app.include_router(job.router, prefix="/api/v1/job")
app.include_router(admin.router, prefix="/api/v1/admin")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(gateway.router, prefix="/api/v1/gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["127.0.0.1"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# @app.middleware("http")
# async def restrict_to_localhost(request: Request, call_next):
#     client_ip = request.client.host
#     if client_ip != "127.0.0.1":
#         raise HTTPException(status_code=403, detail="Forbidden")
#     return await call_next(request)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    logger.info(f"Request took {time.time() - start_time:0.2f} sec")
    return response


@app.middleware("http")
async def circumvent_auth(request: Request, call_next):
    # TODO this is a hotfix, we'd instead like to fix properly in api/routers/auth.py
    if request.url.path == "/api/v1/users/me" and config.auth.passthrough:
        from starlette.responses import JSONResponse

        return JSONResponse({'is_superuser': True})
    else:
        return await call_next(request)


@dataclass
class StatusResponse:
    """Status response model"""

    api: str
    cascade: str
    ecmwf: str


@app.get("/api/v1/status", tags=["status"])
def status() -> StatusResponse:
    """Status endpoint"""
    from forecastbox.config import config

    status = {"api": "up", "cascade": "up", "ecmwf": "up"}

    from cascade.gateway import api, client

    try:
        client.request_response(api.JobProgressRequest(job_ids=[]), config.cascade.cascade_url, timeout_ms=1000)
        status["cascade"] = "up"
    except Exception as e:
        logger.warning(f"Error connecting to Cascade: {e}")
        status["cascade"] = "down"

    # Check connection to model_repository
    import requests

    try:
        response = requests.get(f"{config.api.model_repository}/MANIFEST", timeout=1)
        if response.status_code == 200:
            status["ecmwf"] = "up"
        else:
            status["ecmwf"] = "down"
    except Exception:
        status["ecmwf"] = "down"

    return StatusResponse(**status)


@app.get("/api/v1/share/{job_id}/{dataset_id}", response_class=HTMLResponse, tags=["share"], summary="Share Image")
async def share_image(request: Request, job_id: str, dataset_id: str):
    """Endpoint to share an image from a job and dataset ID."""
    base_url = str(request.base_url).rstrip("/")
    image_url = f"{base_url}/api/v1/job/{job_id}/{dataset_id}"
    return templates.TemplateResponse(
        "share.html", {"request": request, "image_url": image_url, "image_name": f"{job_id}_{dataset_id}"}
    )


frontend = os.path.join(os.path.dirname(__file__), "static")


class SPAStaticFiles(StaticFiles):
    """Custom StaticFiles class to handle SPA routing."""

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as ex:
            if ex.status_code == 404:
                return FileResponse(os.path.join(frontend, "index.html"))
            else:
                raise


app.mount("/", SPAStaticFiles(directory=frontend, html=True, follow_symlink=True), name="static")
