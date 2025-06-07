import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router as api_router
from src.core.config import settings

app = FastAPI(
    title="Middleware SATUSEHAT X DASS21",
    version="0.1.0",
    description="""
    API Middleware untuk:
    - Autentikasi pengguna
    - Menerima hasil kuisioner DASS-21  
    - Mengklasifikasikan tingkat gejala (normal → extremely)  
    - Mendaftarkan pasien ke dalam sistem SATUSEHAT
    - Mendaftarkan kunjungan pasien ke dalam sistem SATUSEHAT
    """,
    openapi_tags=[
        {
            "name": "dass21",
            "description": "Endpoint untuk pemrosesan kuisioner DASS-21"
        }
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api", tags=["dass21"])

if __name__ == "__main__":
    uvicorn.run("main:app", port=settings.PORT, reload=True)
