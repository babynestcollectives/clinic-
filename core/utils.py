"""
utils.py — Shared utility functions for Yazan Abbadi Orthopedic Clinic
"""
from datetime import date, datetime


CLINIC_NAME    = "Yazan Abbadi Orthopedic Clinic"
CLINIC_NAME_AR = "عيادة يزن عبادي للجراحة التقويمية"
CURRENCY       = "JD"

ROLES = ["admin", "surgeon", "receptionist", "accountant", "nurse", "physiotherapist"]

ROLE_LABELS = {
    "admin":            "Administrator",
    "surgeon":          "Orthopedic Surgeon",
    "receptionist":     "Receptionist",
    "accountant":       "Accountant",
    "nurse":            "Nurse",
    "physiotherapist":  "Physiotherapist",
}

BODY_REGIONS = [
    "Knee", "Shoulder", "Hip", "Spine", "Foot & Ankle",
    "Hand & Wrist", "Elbow", "Pelvis", "Ankle", "Pediatric", "Trauma / General",
]

PROCEDURE_TYPES = [
    "Joint Injection (Corticosteroid)", "Joint Injection (Hyaluronic Acid)",
    "PRP Injection", "Joint Aspiration", "Casting / Splinting",
    "Suturing / Wound Closure", "Dressing Change", "Traction",
    "Minor Surgical Procedure", "Nerve Block", "Other",
]

SURGERY_TYPES = [
    "ACL Reconstruction", "PCL Reconstruction", "Meniscus Repair",
    "Meniscectomy (Arthroscopy)", "Knee Arthroscopy",
    "Total Knee Replacement (TKR)", "Unicompartmental Knee Replacement",
    "Total Hip Replacement (THR)", "Hip Arthroscopy",
    "Rotator Cuff Repair", "Shoulder Arthroscopy", "SLAP Repair",
    "Shoulder Arthroplasty", "ORIF — Long Bone", "ORIF — Periarticular",
    "Intramedullary Nailing", "External Fixation",
    "Lumbar Discectomy", "Lumbar Fusion", "Cervical Fusion",
    "Laminectomy", "Carpal Tunnel Release", "Trigger Finger Release",
    "Achilles Repair", "Ankle Arthroscopy", "Foot Fusion",
    "Pediatric Fracture Fixation", "Limb Lengthening", "Other",
]

OUTCOME_SCORES = [
    "VAS Pain Score (0-10)",
    "KOOS (Knee)",
    "Oxford Knee Score",
    "DASH (Upper Limb)",
    "Constant Score (Shoulder)",
    "ODI (Spine)",
    "AOFAS (Foot & Ankle)",
    "Harris Hip Score",
    "EQ-5D",
]

BILLING_CATEGORIES = [
    "Consultation", "Procedure", "Surgery Fee",
    "Imaging / Radiology", "Physiotherapy", "Medication / Supply",
    "Implant", "Cast / Brace", "Lab / Investigation", "Other",
]

PAYMENT_METHODS = ["Cash", "Credit Card", "Bank Transfer", "Insurance", "Cheque"]

EXPENSE_CATEGORIES = [
    "Staff Salary", "Rent / Utilities", "Medical Supplies",
    "Equipment", "Medications", "Insurance Premium",
    "Marketing", "IT / Software", "Maintenance", "Other",
]

REHAB_PHASES = [
    "Phase 0 — Pre-op", "Phase 1 — Acute (0-2 wks)",
    "Phase 2 — Early (2-6 wks)", "Phase 3 — Intermediate (6-12 wks)",
    "Phase 4 — Advanced (3-6 months)", "Phase 5 — Return to Activity (6-12 months)",
]

SPORTS_LEVELS = ["Sedentary", "Recreational", "Amateur Competitive", "Semi-Professional", "Professional"]

SMOKING_STATUS = ["Non-smoker", "Ex-smoker", "Current smoker"]

LATERALITY_OPTIONS = ["Right", "Left", "Bilateral", "N/A"]


def calc_age(dob_str: str) -> str:
    if not dob_str:
        return ""
    try:
        dob   = datetime.strptime(str(dob_str).strip(), "%Y-%m-%d").date()
        today = date.today()
        age   = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return f"{age} yrs"
    except Exception:
        return ""


def fmt_currency(amount) -> str:
    try:
        return f"{CURRENCY} {float(amount):,.3f}"
    except Exception:
        return f"{CURRENCY} 0.000"


def today_str() -> str:
    return date.today().isoformat()


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_date(dt_str: str) -> str:
    if not dt_str:
        return "—"
    try:
        return datetime.strptime(dt_str[:10], "%Y-%m-%d").strftime("%d %b %Y")
    except Exception:
        return dt_str or "—"


def role_can(role: str, permission: str) -> bool:
    """Return True if the given role has the given permission."""
    perms = {
        "admin":           {"all"},
        "surgeon":         {"patients", "visits", "procedures", "surgery", "followup", "search", "analytics", "appointments"},
        "receptionist":    {"patients", "appointments", "search", "billing_view"},
        "accountant":      {"accounting", "billing", "expenses", "inventory", "analytics", "search", "patients_view"},
        "nurse":           {"patients_view", "procedures", "visits_view", "inventory", "appointments"},
        "physiotherapist": {"patients_view", "followup", "visits_view", "search"},
    }
    allowed = perms.get(role, set())
    return "all" in allowed or permission in allowed
