from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.routers import (
    auth, map as map_router, rohrbelegung, netzschema, objekte, import_router, users,
    admin_areas, admin_clusters, admin_projects, admin_bauabschnitte, admin_users,
    admin_audit, admin_system, admin_materials, admin_numbering, edit,
)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Tiefbau- & Glasfaser-Infrastrukturplattform",
    version="1.0.0",
    description="Selbstgehostete Plattform zur Verwaltung von Tiefbau-, Glasfaser- und Netzinfrastruktur.",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(map_router.router)
app.include_router(rohrbelegung.router)
app.include_router(netzschema.router)
app.include_router(objekte.router)
app.include_router(import_router.router)
app.include_router(users.router)
app.include_router(admin_areas.router)
app.include_router(admin_clusters.router)
app.include_router(admin_projects.router)
app.include_router(admin_bauabschnitte.router)
app.include_router(admin_users.router)
app.include_router(admin_audit.router)
app.include_router(admin_system.router)
app.include_router(admin_materials.router)
app.include_router(admin_numbering.router)
app.include_router(edit.router)


@app.get("/health")
def health():
    return {"status": "ok"}
