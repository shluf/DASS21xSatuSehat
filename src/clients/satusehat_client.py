import os
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from uuid import uuid4

from src.core.config import settings
import httpx
from fastapi import HTTPException

from src.models.api_models import NewPatient, VisitPayload

# — Env vars untuk OAuth2 —
AUTH_URL     = settings.AUTH_URL
BASE_URL     = settings.BASE_URL
CLIENT_ID    = settings.CLIENT_ID
CLIENT_SECRET= settings.CLIENT_SECRET

# — Cache sederhana untuk token (in-memory) —
_token_cache: Dict[str, Any] = {
    "access_token": None,
    "expires_at": 0.0
}

async def generate_token() -> str:
    """
    POST /accesstoken?grant_type=client_credentials
    Body x-www-form-urlencoded: client_id, client_secret
    Response: { access_token, token_type, expires_in, ... }
    Token berlaku selama expires_in detik (biasanya 3600).
    :contentReference[oaicite:0]{index=0}
    """
    now = time.time()
    # Reuse token jika belum expired (beri buffer 60 detik)
    if _token_cache["access_token"] and now < _token_cache["expires_at"] - 60:
        return _token_cache["access_token"]

    url = f"{AUTH_URL}/accesstoken"
    params = {"grant_type": "client_credentials"}
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(url, params=params, data=data)
    if not r.is_success:
        raise HTTPException(r.status_code, f"Error generating token: {r.text}")

    resp = r.json()
    token = resp.get("access_token")
    expires_in = resp.get("expires_in", 3600)
    if not token:
        raise HTTPException(500, f"No access_token in response: {resp}")

    # Simpan ke cache
    _token_cache["access_token"] = token
    _token_cache["expires_at"] = now + float(expires_in)
    return token

async def _get(resource: str, params: Optional[Dict[str, Any]] = None) -> Dict:
    """
    Helper GET dengan header Authorization otomatis.
    """
    token = await generate_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/fhir+json"
    }
    url = f"{BASE_URL}/{resource}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=headers, params=params)
    if not r.is_success:
        # Error handling untuk GET
        error_detail = ""
        try:
            error_json = r.json()
            error_detail = f"JSON Response: {error_json}"
            print(f"SATUSEHAT GET ERROR ({r.status_code}) for {url}: {error_json}") # Log full JSON error
        except ValueError:
            error_detail = f"Text Response: {r.text}"
            print(f"SATUSEHAT GET ERROR ({r.status_code}) for {url}: {r.text}") # Log text error
        raise HTTPException(r.status_code, f"GET {resource} failed. Detail: {error_detail}")
    return r.json()

async def _post(resource: str, body: Dict[str, Any]) -> Dict:
    """
    Helper POST dengan header Authorization otomatis.
    """
    token = await generate_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/fhir+json"
    }
    url = f"{BASE_URL}/{resource}"
    print(f"SATUSEHAT POST Request to {url}: Body: {body}") # Log the body being sent
    async with httpx.AsyncClient() as client:
        r = await client.post(url, headers=headers, json=body)
    
    if not r.is_success:
        error_detail_str = ""
        error_json = None
        try:
            # Try to parse JSON first, as FHIR OperationOutcome is JSON
            error_json = r.json()
            error_detail_str = f"JSON Response: {error_json}"
            print(f"SATUSEHAT POST ERROR ({r.status_code}) for {url} with body {body}: {error_json}") # Log full JSON error
        except ValueError: # If r.json() fails (not a JSON response)
            error_detail_str = f"Text Response: {r.text}"
            print(f"SATUSEHAT POST ERROR ({r.status_code}) for {url} with body {body}: {r.text}") # Log text error
        
        # Raise HTTPException with potentially more structured error if available
        # The route handler in routes.py will catch this and also log it.
        detail_to_raise = error_json if error_json else r.text # Prefer structured JSON error for detail
        raise HTTPException(r.status_code, f"POST {resource} failed: {detail_to_raise}")
        
    return r.json()

# ——— Patient ———
async def register_patient_satusehat(data: NewPatient) -> Dict:
    """
    Mendaftarkan pasien baru ke SATUSEHAT dengan resource `Patient`
    menggunakan data dari model Pydantic NewPatient.
    """
    patient_body = {
        "resourceType": "Patient",
        "meta": {"profile": ["https://fhir.kemkes.go.id/r4/StructureDefinition/Patient"]},
        "identifier": [{"use": "official", "system": "https://fhir.kemkes.go.id/id/nik", "value": data.nik}],
        "active": True,
        "name": [{"use": "official", "text": data.name}],
        "gender": data.gender,
        "birthDate": data.birthdate,
        "deceasedBoolean": False,
        "address": [],
        "maritalStatus": None,
        "multipleBirthInteger": 0,
        "contact": [],
        "communication": []
    }

    if data.address_line or data.address_city or data.address_postal_code:
        address_fhir = {
            "use": data.address_use or "home", "line": data.address_line or [],
            "city": data.address_city, "postalCode": data.address_postal_code,
            "country": data.address_country or "ID",
            "extension": [{"url": "https://fhir.kemkes.go.id/r4/StructureDefinition/administrativeCode", "extension": []}]
        }
        admin_code_ext = address_fhir["extension"][0]["extension"]
        if data.address_province_code: admin_code_ext.append({"url": "province", "valueCode": data.address_province_code})
        if data.address_city_code: admin_code_ext.append({"url": "city", "valueCode": data.address_city_code})
        if data.address_district_code: admin_code_ext.append({"url": "district", "valueCode": data.address_district_code})
        if data.address_village_code: admin_code_ext.append({"url": "village", "valueCode": data.address_village_code})
        if data.address_rt: admin_code_ext.append({"url": "rt", "valueCode": data.address_rt})
        if data.address_rw: admin_code_ext.append({"url": "rw", "valueCode": data.address_rw})
        if not admin_code_ext: address_fhir.pop("extension")
        patient_body["address"].append(address_fhir)

    if data.marital_status_code:
        patient_body["maritalStatus"] = {
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus", "code": data.marital_status_code, "display": data.marital_status_text or data.marital_status_code}],
            "text": data.marital_status_text or data.marital_status_code
        }
    else: patient_body.pop("maritalStatus")

    if data.contact_name_text and data.contact_telecom_value:
        patient_body["contact"].append({
            "relationship": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0131",
                            "code": data.contact_relationship_code or "N"
                        }
                    ]
                }
            ],
            "name": {"use": "official", "text": data.contact_name_text},
            "telecom": [{"system": data.contact_telecom_system or "phone", "value": data.contact_telecom_value, "use": data.contact_telecom_use or "mobile"}]
        })
    
    patient_body["communication"].append({
        "language": {"coding": [{"system": "urn:ietf:bcp:47", "code": data.communication_language_code or "id-ID", "display": data.communication_language_text or "Indonesian"}], "text": data.communication_language_text or "Indonesian"},
        "preferred": data.communication_preferred if data.communication_preferred is not None else True
    })

    for key in ["address", "contact", "communication"]:
        if not patient_body[key]: patient_body.pop(key)

    # Log before sending to SATUSEHAT
    print(f"Sending NEW Patient FHIR resource to SATUSEHAT: {patient_body}")
    return await _post("Patient", patient_body)

async def get_patient_by_id(patient_id: str) -> Dict:
    """
    GET Patient by ID (Patient/:id) :contentReference[oaicite:1]{index=1}.
    """
    return await _get(f"Patient/{patient_id}")


async def search_patient_by_nik(nik: str) -> List[Dict]:
    """
    GET Patient?identifier=https://fhir.kemkes.go.id/id/nik|{{nik}} :contentReference[oaicite:2]{index=2}.
    Returns list of entries.
    """
    bundle = await _get("Patient", params={"identifier": f"https://fhir.kemkes.go.id/id/nik|{nik}"})
    return bundle.get("entry", [])


# ——— Practitioner ———
async def get_practitioner_by_id(practitioner_id: str) -> Dict:
    """
    GET Practitioner/:id :contentReference[oaicite:3]{index=3}.
    """
    return await _get(f"Practitioner/{practitioner_id}")


async def search_practitioner_by_nik(nik: str) -> List[Dict]:
    """
    GET Practitioner?identifier=https://fhir.kemkes.go.id/id/nik|{{nik}} :contentReference[oaicite:4]{index=4}.
    """
    bundle = await _get("Practitioner", params={"identifier": f"https://fhir.kemkes.go.id/id/nik|{nik}"})
    return bundle.get("entry", [])


async def search_practitioner(
    name: Optional[str] = None,
    birthdate: Optional[str] = None,
    gender: Optional[str] = None
) -> List[Dict]:
    """
    GET Practitioner?name={name}&birthdate={birthdate}&gender={gender} :contentReference[oaicite:5]{index=5}.
    """
    params: Dict[str, str] = {}
    if name:      params["name"] = name
    if birthdate: params["birthdate"] = birthdate
    if gender:    params["gender"] = gender
    bundle = await _get("Practitioner", params=params)
    return bundle.get("entry", [])


# ——— Organization ———
async def create_organization(body: Dict[str, Any]) -> Dict:
    """
    POST Organization :contentReference[oaicite:6]{index=6}.
    Body must follow FHIR Organization profile.
    """
    return await _post("Organization", body)


# ——— Location ———
async def create_location(body: Dict[str, Any]) -> Dict:
    """
    POST Location :contentReference[oaicite:7]{index=7}.
    Body must follow FHIR Location profile.
    """
    return await _post("Location", body)

async def get_location_by_id(location_id: str) -> Dict:
    """
    GET Location/:id.
    """
    return await _get(f"Location/{location_id}")

async def get_all_locations_by_org(organization_id: str) -> List[Dict]:
    """
    GET Location?organization={{organization_id}}.
    Returns list of location entries for a given organization.
    """
    bundle = await _get("Location", params={"organization": organization_id})
    return bundle.get("entry", [])

# ——— Encounter ———
async def create_encounter(data: VisitPayload) -> Dict:
    """
    Membuat resource Encounter (kunjungan) baru untuk pasien yang sudah terdaftar.
    Body must follow FHIR Encounter profile.
    """
    patient_id = data.patient_id
    practitioner_id = settings.PRACTITIONER_ID
    location_id = data.location_id # Use location_id from payload
    organization_id = settings.ORGANIZATION_ID

    # --- Fetch complete and accurate data from SATUSEHAT to avoid mismatches ---
    try:
        patient_data = await get_patient_by_id(patient_id)
        # Safely extract patient name from the list of names
        patient_name_display = next((name.get('text') for name in patient_data.get('name', []) if name.get('text')), data.patient_name)
    except HTTPException as e:
        print(f"Error fetching patient data for ID {patient_id}: {e.detail}")
        raise HTTPException(status_code=404, detail=f"Patient with ID {patient_id} not found or error fetching data from SATUSEHAT.")

    try:
        practitioner_data = await get_practitioner_by_id(practitioner_id)
        # Safely extract practitioner name
        practitioner_name = next((name.get('text') for name in practitioner_data.get('name', []) if name.get('text')), "Practitioner Name Not Found")
    except HTTPException as e:
        print(f"Error fetching practitioner data for ID {practitioner_id}: {e.detail}")
        raise HTTPException(status_code=404, detail=f"Practitioner with ID {practitioner_id} not found or error fetching data from SATUSEHAT.")

    try:
        location_data = await get_location_by_id(location_id)
        # Safely extract location name
        location_name = location_data.get('name', "Location Name Not Found")
    except HTTPException as e:
        print(f"Error fetching location data for ID {location_id}: {e.detail}")
        raise HTTPException(status_code=404, detail=f"Location with ID {location_id} not found or error fetching data from SATUSEHAT.")
    
    print(f"Creating visit for Patient: {patient_name_display} (ID: {patient_id})")
    print(f"With Practitioner: {practitioner_name} (ID: {practitioner_id})")
    print(f"At Location: {location_name} (ID: {location_id})")

    start_time = datetime.now(timezone.utc).isoformat()
    encounter_registration_id = str(uuid4())

    encounter_body = {
        "resourceType": "Encounter",
        "identifier": [
            {
                "system": f"http://sys-ids.kemkes.go.id/encounter/{organization_id}",
                "value": encounter_registration_id
            }
        ],
        "status": "arrived",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB",
            "display": "ambulatory"
        },
        "subject": {
            "reference": f"Patient/{patient_id}",
            "display": patient_name_display
        },
        "participant": [
            {
                "type": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                                "code": "ATND",
                                "display": "attender"
                            }
                        ]
                    }
                ],
                "individual": {
                    "reference": f"Practitioner/{practitioner_id}",
                    "display": practitioner_name
                }
            }
        ],
        "period": {"start": start_time},
        "location": [
            {
                "location": {
                    "reference": f"Location/{location_id}",
                    "display": location_name
                },
                "period": { "start": start_time },
                "extension": [
                    {
                        "url": "https://fhir.kemkes.go.id/r4/StructureDefinition/ServiceClass",
                        "extension": [
                            {
                                "url": "value",
                                "valueCodeableConcept": {
                                    "coding": [
                                        {
                                            "system": "http://terminology.kemkes.go.id/CodeSystem/locationServiceClass-Outpatient",
                                            "code": "reguler", "display": "Kelas Reguler"
                                        }
                                    ]
                                }
                            },
                            {
                                "url": "upgradeClassIndicator",
                                "valueCodeableConcept": {
                                    "coding": [
                                        {
                                            "system": "http://terminology.kemkes.go.id/CodeSystem/locationUpgradeClass",
                                            "code": "kelas-tetap", "display": "Kelas Tetap Perawatan"
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
        ],
        "statusHistory": [
            {
                "status": "arrived", 
                "period": { "start": start_time }
            }
        ],
        "serviceProvider": {"reference": f"Organization/{organization_id}"}
    }
    
    print(f"Creating encounter with body: {encounter_body}")
    return await _post("Encounter", encounter_body)