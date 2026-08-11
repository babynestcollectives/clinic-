from core.database import get_supabase
from datetime import datetime
from collections import Counter

supabase = get_supabase()

SPECIALTIES = [
    "Arthroplasty",
    "General Orthopaedics",
    "Sport Orthopaedics",
    "Trauma",
    "Paediatric Orthopaedics",
    "Fellowship – Arthroscopy & Sports Medicine",
]

# ── HOSPITAL MANAGEMENT ───────────────────────────────────────────────────────
def get_hospitals() -> dict:
    res = supabase.table('hospitals').select('code, name, type').eq('active', 1).order('code').execute()
    return {r["code"]: r["name"] for r in res.data} if res.data else {}

def get_hospitals_full() -> list:
    res = supabase.table('hospitals').select('code, name, type, active').order('code').execute()
    return res.data if res.data else []

def add_hospital(code: str, name: str, htype: str) -> bool:
    code = code.strip().upper()
    if not code or not name.strip():
        return False
    try:
        supabase.table('hospitals').insert({"code": code, "name": name.strip(), "type": htype.strip()}).execute()
        return True
    except:
        return False

def update_hospital(code: str, name: str, htype: str):
    supabase.table('hospitals').update({"name": name.strip(), "type": htype.strip()}).eq('code', code).execute()

def delete_hospital(code: str):
    supabase.table('hospitals').delete().eq('code', code).execute()

def toggle_hospital(code: str, active: bool):
    supabase.table('hospitals').update({"active": 1 if active else 0}).eq('code', code).execute()

def hospital_name(code: str) -> str:
    res = supabase.table('hospitals').select('name').eq('code', code).execute()
    return res.data[0]["name"] if res.data else code

# ── CRUD ─────────────────────────────────────────────────────────────────────
def add_case(data: dict) -> int:
    # Patient name handling: we need to resolve or create patient_id
    pt_name = data.pop('patient_name', '')
    mrn = data.pop('mrn', None)
    age = data.pop('age', None)
    gender = data.pop('gender', None)
    
    # Try finding patient
    q = supabase.table('patients').select('id').eq('name', pt_name)
    if mrn: q = q.eq('mrn', mrn)
    pt_res = q.execute()
    
    if pt_res.data:
        pt_id = pt_res.data[0]['id']
    else:
        new_pt = supabase.table('patients').insert({
            'name': pt_name, 'mrn': mrn, 'age': age, 'gender': gender, 'is_clinic_patient': False
        }).execute()
        pt_id = new_pt.data[0]['id'] if new_pt.data else None
        
    data['patient_id'] = pt_id
    res = supabase.table('surgical_cases').insert(data).execute()
    return res.data[0]['id'] if res.data else None

def update_case(case_id: int, data: dict):
    # Patient handling
    pt_name = data.pop('patient_name', '')
    mrn = data.pop('mrn', None)
    age = data.pop('age', None)
    gender = data.pop('gender', None)
    
    # Find existing case to get patient_id
    case_res = supabase.table('surgical_cases').select('patient_id').eq('id', case_id).execute()
    if case_res.data:
        pt_id = case_res.data[0]['patient_id']
        supabase.table('patients').update({
            'name': pt_name, 'mrn': mrn, 'age': age, 'gender': gender
        }).eq('id', pt_id).execute()
        
    data["updated_at"] = datetime.now().isoformat()
    supabase.table('surgical_cases').update(data).eq('id', case_id).execute()

def delete_case(case_id: int):
    supabase.table('surgical_followups').delete().eq('case_id', case_id).execute()
    supabase.table('surgical_cases').delete().eq('id', case_id).execute()

def get_case(case_id: int):
    res = supabase.table('surgical_cases').select('*, patients(name, mrn, age, gender)').eq('id', case_id).execute()
    if not res.data: return {}
    case = res.data[0]
    pt = case.pop('patients', {}) or {}
    if pt:
        case['patient_name'] = pt.get('name')
        case['mrn'] = pt.get('mrn')
        case['age'] = pt.get('age')
        case['gender'] = pt.get('gender')
    return case

def search_cases(
    keywords: str = "",
    hospital: str = "",
    specialty: str = "",
    date_from: str = "",
    date_to: str = "",
    is_fellowship: int = -1,
    complication_only: bool = False,
) -> list:
    q = supabase.table('surgical_cases').select('*, patients(name, mrn)')
    
    if hospital: q = q.eq('hospital_code', hospital)
    if specialty: q = q.eq('specialty', specialty)
    if date_from: q = q.gte('case_date', date_from)
    if date_to: q = q.lte('case_date', date_to)
    if is_fellowship >= 0: q = q.eq('is_fellowship', is_fellowship)
    if complication_only: q = q.neq('complications', '').not_.is_('complications', 'null')
    
    # Text search is tricky with supabase-py without RPC, we'll fetch and filter in memory if keywords exist
    res = q.order('case_date', desc=True).execute()
    cases = res.data if res.data else []
    
    formatted_cases = []
    for c in cases:
        pt = c.pop('patients', {}) or {}
        c['patient_name'] = pt.get('name', '')
        c['mrn'] = pt.get('mrn', '')
        formatted_cases.append(c)
        
    if keywords.strip():
        filtered = []
        kws = keywords.lower().split()
        for c in formatted_cases:
            text = f"{c.get('patient_name','')} {c.get('mrn','')} {c.get('diagnosis','')} {c.get('procedure','')} {c.get('findings','')} {c.get('notes','')} {c.get('complications','')} {c.get('graft_type','')} {c.get('implant','')}".lower()
            if all(kw in text for kw in kws):
                filtered.append(c)
        return filtered
    
    return formatted_cases

def get_all_cases() -> list:
    return search_cases()

# ── STATISTICS ───────────────────────────────────────────────────────────────
def _tokenize_and_count(values: list, limit: int = 20) -> list:
    counts = Counter()
    canonical = {}
    for val in values:
        if not val or not val.strip(): continue
        for token in val.split("+"):
            token = token.strip()
            if not token: continue
            key = token.lower()
            counts[key] += 1
            if key not in canonical:
                canonical[key] = token[0].upper() + token[1:]
    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    return [{"procedure" if limit==20 else "diagnosis": canonical[k], "n": v} for k, v in sorted_items] # Hacky but works for this usage

def stats_summary() -> dict:
    cases = get_all_cases()
    total = len(cases)
    fellowship = sum(1 for c in cases if c.get('is_fellowship') == 1)
    complications = sum(1 for c in cases if c.get('complications'))
    
    by_hosp = Counter(c.get('hospital_code') for c in cases if c.get('hospital_code'))
    by_spec = Counter(c.get('specialty') for c in cases if c.get('specialty'))
    by_year = Counter(c.get('case_date', '')[:4] for c in cases if c.get('case_date'))
    by_month = Counter(c.get('case_date', '')[:7] for c in cases if c.get('case_date'))
    by_side = Counter(c.get('side') for c in cases if c.get('side'))
    by_anaesthesia = Counter(c.get('anaesthesia') for c in cases if c.get('anaesthesia'))
    by_role = Counter(c.get('role') for c in cases if c.get('role'))
    
    durs = [c.get('duration_min') for c in cases if c.get('duration_min')]
    avg_duration = sum(durs) / len(durs) if durs else 0
    
    procs = [c.get('procedure') for c in cases]
    diags = [c.get('diagnosis') for c in cases]
    
    hosp_map = get_hospitals()
    
    return {
        "total": total,
        "fellowship": fellowship,
        "specialist": total - fellowship,
        "complications": complications,
        "complication_rate": round(complications / total * 100, 1) if total else 0,
        "by_hospital": [{"hospital_code": k, "hospital_name": hosp_map.get(k, k), "n": v} for k, v in by_hosp.most_common()],
        "by_specialty": [{"specialty": k, "n": v} for k, v in by_spec.most_common()],
        "by_procedure": _tokenize_and_count(procs),
        "by_diagnosis": _tokenize_and_count(diags),
        "by_year": [{"yr": k, "n": v} for k, v in by_year.most_common()],
        "by_month": [{"mo": k, "n": v} for k, v in by_month.most_common()],
        "by_side": [{"side": k, "n": v} for k, v in by_side.most_common()],
        "by_anaesthesia": [{"anaesthesia": k, "n": v} for k, v in by_anaesthesia.most_common()],
        "by_role": [{"role": k, "n": v} for k, v in by_role.most_common()],
        "avg_duration": round(avg_duration, 1) if avg_duration else None
    }

# ── FOLLOW-UPS ────────────────────────────────────────────────────────────────
def add_followup(case_id: int, fu_date: str, notes: str, outcome: str) -> int:
    res = supabase.table('surgical_followups').insert({
        "case_id": case_id, "fu_date": fu_date, "notes": notes, "outcome": outcome
    }).execute()
    return res.data[0]['id'] if res.data else None

def get_followups(case_id: int) -> list:
    res = supabase.table('surgical_followups').select('*').eq('case_id', case_id).order('fu_date', desc=True).execute()
    return res.data if res.data else []

def get_patient_surgical_cases(patient_id: int) -> list:
    supabase = get_supabase()
    res = supabase.table('surgical_cases').select('*, hospitals(name)').eq('patient_id', patient_id).order('case_date', desc=True).execute()
    cases = res.data or []
    for c in cases:
        h = c.pop('hospitals', {}) or {}
        c['hospital_name'] = h.get('name', 'Unknown')
    return cases
