from fastapi import APIRouter, Depends, HTTPException, status

from src.models.user_models import UserPublic
from src.models.api_models import NewPatient, VisitPayload
from src.core.security import get_current_user
from src.core.config import settings
from src.clients.satusehat_client import (
    create_encounter,
    register_patient_satusehat,
    search_patient_by_nik,
    get_all_locations_by_org,
)

router = APIRouter()

@router.post("/register-patient", summary="Daftarkan atau cari pasien by NIK", tags=["registrasi"])
async def register_patient(data: NewPatient, current_user: UserPublic = Depends(get_current_user)):
    """
    Mencari pasien berdasarkan NIK. Jika tidak ada, mendaftarkan pasien baru.
    Mengembalikan resource Patient FHIR yang ditemukan atau yang baru dibuat.
    """
    try:
        patient_entries = await search_patient_by_nik(data.nik) 

        patient_resource = None
        
        if patient_entries:
            patient_resource = patient_entries[0].get("resource")
            if not patient_resource:
                raise HTTPException(status_code=500, detail="Found patient entry but no resource field in SATUSEHAT response.")
        else:
            patient_resource = await register_patient_satusehat(data)

        if not patient_resource or not patient_resource.get("id"):
            raise HTTPException(status_code=500, detail="Failed to obtain patient resource.")

        return {
            "message": "Patient lookup/creation successful.",
            "patient_id": patient_resource.get("id"),
            "patient_resource": patient_resource
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        print(f"ERROR in /register-patient endpoint for user {current_user.email}:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error during patient registration. Details: {str(e)}")

@router.get("/locations", summary="Dapatkan semua lokasi berdasarkan ID Organisasi", tags=["lokasi"], response_model=list)
async def get_locations(current_user: UserPublic = Depends(get_current_user)):
    """
    Mengambil daftar semua lokasi (ruangan, poli, dll.) yang terdaftar
    untuk organisasi yang dikonfigurasi dalam sistem.
    """
    try:
        organization_id = settings.ORGANIZATION_ID
        if not organization_id:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="ORGANIZATION_ID tidak dikonfigurasi di server."
            )
            
        location_entries = await get_all_locations_by_org(organization_id)
        
        return [
            {
                "id": entry.get("resource", {}).get("id"),
                "name": entry.get("resource", {}).get("name"),
                "description": entry.get("resource", {}).get("description")
            }
            for entry in location_entries
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error while fetching locations. Details: {str(e)}"
        )

@router.post("/create-visit", summary="Buat kunjungan (Encounter) baru", tags=["registrasi"])
async def create_visit(data: VisitPayload, current_user: UserPublic = Depends(get_current_user)):
    """
    Membuat resource Encounter (kunjungan) baru untuk pasien yang sudah terdaftar.
    """
    try:
        encounter = await create_encounter(data)
        return {
            "message": f"Visit successfully created for patient {data.patient_id}.",
            "encounter_id": encounter.get("id"),
            "encounter_resource": encounter
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error during visit creation. Details: {str(e)}") 