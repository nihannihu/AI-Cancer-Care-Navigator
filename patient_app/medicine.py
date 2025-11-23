from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class Medication:
    def __init__(
        self, 
        medication_id: str,
        drug_name: str, 
        dosage: str, 
        frequency: int, # times per day
        start_date: str, # YYYY-MM-DD
        end_date: str,   # YYYY-MM-DD
        current_inventory_count: int
    ):
        self.medication_id = medication_id
        self.drug_name = drug_name
        self.dosage = dosage
        self.frequency = frequency
        self.start_date = start_date
        self.end_date = end_date
        self.current_inventory_count = current_inventory_count
        self.logs = [] # List of timestamps when taken

    def mark_taken(self):
        self.logs.append(datetime.now().isoformat())
        self.current_inventory_count -= 1

class AdherenceSystem:
    def __init__(self):
        self.medications: Dict[str, Medication] = {}

    def add_medication(self, med: Medication):
        self.medications[med.medication_id] = med

    def check_inventory(self, medication_id: str) -> bool:
        """
        Returns True if current_inventory_count <= (3 * daily_dosage).
        This means we have 3 days or less supply.
        """
        med = self.medications.get(medication_id)
        if not med:
            return False
        
        daily_dosage = med.frequency # Assuming 1 pill per dose for simplicity
        threshold = 3 * daily_dosage
        return med.current_inventory_count <= threshold

    def calculate_compliance(self, medication_id: str) -> float:
        """
        (Total Taken / Total Scheduled) * 100
        """
        med = self.medications.get(medication_id)
        if not med:
            return 0.0

        start = datetime.strptime(med.start_date, "%Y-%m-%d")
        now = datetime.now()
        days_elapsed = (now - start).days + 1
        
        if days_elapsed <= 0:
            return 100.0

        total_scheduled = days_elapsed * med.frequency
        total_taken = len(med.logs)
        
        if total_scheduled == 0:
            return 100.0
            
        return (total_taken / total_scheduled) * 100.0

    def notify_doctor(self, patient_id: str, medication_id: str):
        """
        Trigger an alert function if compliance < 80%.
        """
        med = self.medications.get(medication_id)
        drug_name = med.drug_name if med else "Unknown"
        logger.warning(f"ALERT: Patient {patient_id} has low adherence (<80%) for {drug_name}.")
        # In real app, send email/SMS to doctor

    def generate_refill_notification(self, medication_id: str) -> Optional[str]:
        """
        Generates a text template: 'Time for [Drug Name]. You have [X] pills left. Please refill soon if needed.'
        """
        med = self.medications.get(medication_id)
        if not med:
            return None
            
        return f"Time for {med.drug_name}. You have {med.current_inventory_count} pills left. Please refill soon if needed."

    def check_and_alert(self, patient_id: str, medication_id: str) -> Dict[str, Any]:
        """
        Orchestrates checks and returns alerts.
        """
        compliance = self.calculate_compliance(medication_id)
        inventory_low = self.check_inventory(medication_id)
        
        alerts = []
        if compliance < 80.0:
            self.notify_doctor(patient_id, medication_id)
            alerts.append("Low adherence detected. Doctor notified.")
            
        if inventory_low:
            msg = self.generate_refill_notification(medication_id)
            alerts.append(msg)
            
        return {
            "compliance": compliance,
            "inventory_low": inventory_low,
            "alerts": alerts
        }
