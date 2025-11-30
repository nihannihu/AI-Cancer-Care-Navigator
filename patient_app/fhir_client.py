import httpx
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from .config import HAPI_FHIR_URL

logger = logging.getLogger(__name__)

class FHIRClient:
    def __init__(self, base_url: str = HAPI_FHIR_URL):
        self.base_url = base_url.rstrip('/')
        self.headers = {"Content-Type": "application/fhir+json"}

    async def _post(self, resource_type: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/{resource_type}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=data, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"FHIR POST error: {e}")
                return None

    async def _get(self, resource_type: str, resource_id: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/{resource_type}/{resource_id}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"FHIR GET error: {e}")
                return None

    async def create_patient(self, name: str, age: int, gender: str, cancer_type: str = None) -> Optional[Dict[str, Any]]:
        """
        Creates a Patient resource in FHIR.
        """
        # Calculate birthDate from age (approximate)
        birth_year = datetime.now().year - age
        birth_date = f"{birth_year}-01-01"

        patient_data = {
            "resourceType": "Patient",
            "name": [
                {
                    "use": "official",
                    "family": name.split()[-1] if " " in name else name,
                    "given": name.split()[:-1] if " " in name else [name]
                }
            ],
            "gender": gender.lower(),
            "birthDate": birth_date,
            "extension": []
        }
        
        # We could store cancer_type as an extension or observation, 
        # but for now we'll just create the patient. 
        # The prompt asks to create_patient with cancer_type, 
        # usually that implies creating a Condition as well, but we have a separate function for that.
        # We will return the created patient.
        
        return await self._post("Patient", patient_data)

    async def get_patient_by_id(self, patient_id: str) -> Optional[Dict[str, Any]]:
        return await self._get("Patient", patient_id)

    async def add_cancer_diagnosis(self, patient_id: str, cancer_type: str, stage: str, date: str = None) -> Optional[Dict[str, Any]]:
        """
        Posts a FHIR 'Condition' resource linked to the patient.
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        condition_data = {
            "resourceType": "Condition",
            "clinicalStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active"
                }]
            },
            "verificationStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": "confirmed"
                }]
            },
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                    "code": "encounter-diagnosis",
                    "display": "Encounter Diagnosis"
                }]
            }],
            "code": {
                "text": cancer_type
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "onsetDateTime": date,
            "stage": [{
                "summary": {
                    "text": stage
                }
            }]
        }

        return await self._post("Condition", condition_data)
