from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, ingest, sites
from app.ai.routers import website_chat, metric_chat
from app.api import visit_frequency
from app.db import init_db, migrate_db
import os
from dotenv import load_dotenv
from app.cors_static import CORSEnabledStaticFiles
load_dotenv()

app = FastAPI()

# Load environment variables
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# ------------------------
# CORS Configuration
# ------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------
# Startup
# ------------------------
@app.on_event("startup")
def startup_event():
    init_db()
    migrate_db()  # Run migrations to add last_updated column if needed

# ------------------------
# Routers
# ------------------------
app.include_router(auth.router, prefix="/api")
app.include_router(ingest.router, prefix="/ingest")
app.include_router(sites.router, prefix="/api")
app.include_router(website_chat.router, prefix="/ai")
app.include_router(metric_chat.router, prefix="/ai")
app.include_router(visit_frequency.router, prefix="/api")
# AI insights router (returns recent insights per site)
try:
    from app.ai.routers import ai_insights
    app.include_router(ai_insights.router, prefix="")
except Exception as exc:
    print(f"Warning: failed to load ai_insights router: {exc}")

# ------------------------
# Client-Side SDK (OPEN CORS)
# ------------------------

@app.options("/stats-config.js")
def client_sdk_preflight():
    return Response(
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400",
        },
    )

@app.get("/stats-config.js")
def serve_client_sdk(request: Request, siteId: str = None, siteKey: str = None):
    backend_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

    js_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "client-side-sdk.js"
    )

    with open(js_path, "r", encoding="utf-8") as f:
        js_content = f.read()

    # Inject site configuration if provided via query parameters
    if siteId and siteKey:
        # Inject config before the main loader script
        config_injection = f'''window.analytiqSiteId = "{siteId}";
  window.analytiqSiteKey = "{siteKey}";'''
        # Insert config right after the opening IIFE
        js_content = js_content.replace(
            "(function() {\n  'use strict';",
            f"(function() {{\n  'use strict';\n\n  // Injected site configuration\n  {config_injection}\n"
        )

    return Response(
        content=js_content,
        media_type="application/javascript",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )

# ------------------------
# Test Page
# ------------------------
@app.get("/test")
def serve_test_page():
    test_html_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "test-sdk.html"
    )

    with open(test_html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    return Response(content=html_content, media_type="text/html")

# ------------------------
# Static Client-Side SDK
# ------------------------
client_sdk_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "client-side-sdk"
)
app.mount(
    "/client-side-sdk",
    CORSEnabledStaticFiles(directory=client_sdk_path),
    name="client-side-sdk",
)


