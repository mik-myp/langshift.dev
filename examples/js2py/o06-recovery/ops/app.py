import hashlib
import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
import psycopg

from ops.cluster import checked_root, connect


class ProjectInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    name: str = Field(min_length=1,max_length=120)

    @field_validator("name")
    @classmethod
    def nonblank(cls,value):
        if not value.strip(): raise ValueError("name must not be blank")
        return value


class ProjectInputV2(ProjectInput):
    description: str | None = Field(default=None,max_length=500)


def create_app():
    root = checked_root(os.environ["OPS_LAB_ROOT"])
    database = os.environ.get("OPS_DATABASE", "source")
    release = os.environ.get("OPS_RELEASE", "v1")
    if release not in {"v1", "v2"}: raise RuntimeError("OPS_RELEASE must be v1 or v2")
    with connect(root,database,"lab_app") as conn:
        revision = conn.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    if revision not in {"006_task_operations", "007_project_description"} or (release=="v2" and revision!="007_project_description"):
        raise RuntimeError("Schema is incompatible; run the approved migration before starting this release")
    app = FastAPI(title="Operations learning slice",version=release)
    app.state.root,app.state.database = root,database

    def db():
        return connect(root,database,"lab_app")

    def actor(request:Request):
        header=request.headers.get("authorization","")
        scheme,_,token=header.partition(" ")
        if scheme.lower()!="bearer" or not token or len(token)>256 or not token.isascii():
            raise HTTPException(401,"Authentication required",headers={"WWW-Authenticate":"Bearer"})
        digest=hashlib.sha256(token.encode("ascii")).hexdigest()
        with db() as conn:
            row=conn.execute("""SELECT u.id FROM auth_sessions s JOIN users u ON u.id=s.user_id
              WHERE s.token_digest=%s AND s.revoked_at IS NULL AND s.expires_at>now()
              AND u.is_active AND s.auth_version=u.auth_version""",(digest,)).fetchone()
        if row is None:raise HTTPException(401,"Authentication required",headers={"WWW-Authenticate":"Bearer"})
        return row[0]

    @app.exception_handler(RequestValidationError)
    def validation_error(request,error):
        return JSONResponse(status_code=422,content={"detail":[{"loc":list(item["loc"]),"type":item["type"]} for item in error.errors()]})

    @app.exception_handler(psycopg.Error)
    def database_error(request,error):
        return JSONResponse(status_code=503,content={"detail":"Database unavailable"})

    @app.get("/health/live")
    def live():return {"status":"ok"}

    @app.get("/health/ready")
    def ready():
        with db() as conn:conn.execute("SELECT 1")
        return {"status":"ready"}

    @app.get("/projects/{project_id}")
    def project(project_id:int,user_id:int=Depends(actor)):
        columns="p.id,p.name,p.description" if release=="v2" else "p.id,p.name"
        with db() as conn:
            row=conn.execute(f"SELECT {columns} FROM projects p JOIN project_members m ON m.project_id=p.id WHERE p.id=%s AND m.user_id=%s",(project_id,user_id)).fetchone()
        if row is None:raise HTTPException(404,"Project not found")
        result={"id":row[0],"name":row[1]}
        if release=="v2":result["description"]=row[2]
        return result

    def insert(payload,user_id):
        with db() as conn:
            if release=="v2":
                row=conn.execute("INSERT INTO projects(name,description,created_by) VALUES (%s,%s,%s) RETURNING id",(payload.name,payload.description,user_id)).fetchone()
            else:
                row=conn.execute("INSERT INTO projects(name,created_by) VALUES (%s,%s) RETURNING id",(payload.name,user_id)).fetchone()
            conn.execute("INSERT INTO project_members(project_id,user_id,role) VALUES (%s,%s,'owner')",(row[0],user_id))
        return {"id":row[0],"name":payload.name}

    if release=="v2":
        @app.post("/projects",status_code=201)
        def create(payload:ProjectInputV2,user_id:int=Depends(actor)):
            return {**insert(payload,user_id),"description":payload.description}
    else:
        @app.post("/projects",status_code=201)
        def create(payload:ProjectInput,user_id:int=Depends(actor)):
            return insert(payload,user_id)
    return app
