from typing import Optional
from pydantic import BaseModel, Field, conint


class DASS21Payload(BaseModel):
    """
    Payload untuk kuisioner DASS-21.
    Skor tiap item: 0 (tidak pernah) hingga 3 (hampir selalu).
    """
    depression: list[conint(ge=0, le=3)] = Field( # type: ignore
        ..., 
        description="7 nilai skor depresi (Q3, Q5, Q10, Q13, Q16, Q17, Q21)",
        example=[0,1,2,3,0,1,2]
    )
    anxiety: list[conint(ge=0, le=3)] = Field( # type: ignore
        ..., 
        description="7 nilai skor kecemasan (Q2, Q4, Q7, Q9, Q15, Q19, Q20)",
        example=[1,1,1,1,1,1,1]
    )
    stress: list[conint(ge=0, le=3)] = Field( # type: ignore
        ..., 
        description="7 nilai skor stres (Q1, Q6, Q8, Q11, Q12, Q14, Q18)",
        example=[2,2,2,2,2,2,2]
    )
    user_id: Optional[str] = Field(
        None,
        description="ID unik pengguna untuk rekam jejak (DEPRECATED if authenticated, will use current user)"
    )

class Recommendation(BaseModel):
    """Response berisi level, pesan, dan daftar provider."""
    level: str = Field(..., description="Kategori severity (normal/mild/...)", example="moderate")
    message: str = Field(..., description="Saran tindak lanjut berdasarkan level", example="Disarankan sesi dengan psikolog.")
    advice: str = Field(..., description="Saran dan rekomendasi detail berdasarkan kondisi mental.", example="Cobalah untuk menerapkan teknik relaksasi...")
    available_facilities: Optional[list[dict]] = Field(None, description="Fasilitas yang tersedia untuk registrasi kunjungan (jika level severe/extremely)")

class NewPatient(BaseModel):
    nik: str = Field(..., example="1234567890123456")
    name: str = Field(..., example="Budi Santoso")
    gender: str = Field(..., example="male", description="male | female | other | unknown")
    birthdate: str = Field(..., example="1990-01-01", description="YYYY-MM-DD format")

    # Address details
    address_use: Optional[str] = Field("home", example="home", description="home | work | temp | old | billing")
    address_line: Optional[list[str]] = Field(None, example=["Jl. Sudirman No.Kav 28"])
    address_city: Optional[str] = Field(None, example="Jakarta")
    address_postal_code: Optional[str] = Field(None, example="12920")
    address_country: Optional[str] = Field("ID", example="ID")
    # Administrative codes for address extension
    address_province_code: Optional[str] = Field(None, example="31")
    address_city_code: Optional[str] = Field(None, example="3171")
    address_district_code: Optional[str] = Field(None, example="317101")
    address_village_code: Optional[str] = Field(None, example="3171010001")
    address_rt: Optional[str] = Field(None, example="001")
    address_rw: Optional[str] = Field(None, example="002")

    # Marital Status
    # See http://terminology.hl7.org/CodeSystem/v3-MaritalStatus
    marital_status_code: Optional[str] = Field(None, example="M", description="A | D | I | L | M | P | S | T | U | W")
    marital_status_text: Optional[str] = Field(None, example="Married") # Will be used if code provided

    # Contact Person (Simplified for one contact)
    contact_relationship_code: Optional[str] = Field(None, example="C", description="Emergency Contact, etc. from http://terminology.hl7.org/CodeSystem/v2-0131")
    contact_name_text: Optional[str] = Field(None, example="Jane Doe")
    contact_telecom_system: Optional[str] = Field("phone", example="phone")
    contact_telecom_value: Optional[str] = Field(None, example="08123456789")
    contact_telecom_use: Optional[str] = Field("mobile", example="mobile")

    # Communication Language (defaults to Indonesian if not provided)
    communication_language_code: Optional[str] = Field("id-ID", example="id-ID")
    communication_language_text: Optional[str] = Field("Indonesian", example="Indonesian")
    communication_preferred: Optional[bool] = Field(True)


class VisitPayload(BaseModel):
    """Payload untuk membuat kunjungan baru."""
    patient_id: str = Field(..., description="ID Pasien dari SATUSEHAT yang didapat dari endpoint registrasi/pencarian.")
    patient_name: str = Field(..., description="Nama lengkap pasien untuk display di resource Encounter.")
    location_id: str = Field(..., description="ID Lokasi (ruang/poli) dari SATUSEHAT tempat kunjungan akan dibuat.") 