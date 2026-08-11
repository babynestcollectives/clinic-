import sqlite3
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load secrets from .streamlit/secrets.toml if possible, or expect them in .env
try:
    import toml
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        secrets = toml.load(secrets_path)
        url = secrets.get("supabase", {}).get("url")
        key = secrets.get("supabase", {}).get("key")
    else:
        load_dotenv()
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
except ImportError:
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

if not url or not key or url == "YOUR_SUPABASE_URL_HERE":
    print("ERROR: Supabase URL and Key are missing. Please add them to .streamlit/secrets.toml")
    exit(1)

supabase: Client = create_client(url, key)

CLINIC_DB_PATH = "../clinic_app_v2/clinic_app/clinic.db"
SURGERY_DB_PATH = "../surgical_logbook_app_3/surgical_app/surgical_logbook.db"

def get_clinic_conn():
    if not os.path.exists(CLINIC_DB_PATH):
        print(f"ERROR: Clinic DB not found at {CLINIC_DB_PATH}")
        return None
    conn = sqlite3.connect(CLINIC_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_surgery_conn():
    if not os.path.exists(SURGERY_DB_PATH):
        print(f"ERROR: Surgical DB not found at {SURGERY_DB_PATH}")
        return None
    conn = sqlite3.connect(SURGERY_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_users():
    print("migrating users...")
    conn = get_clinic_conn()
    if not conn: return
    
    rows = conn.execute("SELECT * FROM users").fetchall()
    for row in rows:
        data = dict(row)
        # Check if exists
        exists = supabase.table('users').select('id').eq('username', data['username']).execute()
        if not exists.data:
            supabase.table('users').insert(data).execute()
    print(f"Users migrated: {len(rows)}")

def migrate_hospitals():
    print("migrating hospitals...")
    conn = get_surgery_conn()
    if not conn: return
    rows = conn.execute("SELECT * FROM hospitals").fetchall()
    for row in rows:
        data = dict(row)
        exists = supabase.table('hospitals').select('code').eq('code', data['code']).execute()
        if not exists.data:
            supabase.table('hospitals').insert(data).execute()
    print(f"Hospitals migrated: {len(rows)}")

def migrate_patients():
    print("migrating clinic patients...")
    conn = get_clinic_conn()
    if not conn: return
    rows = conn.execute("SELECT * FROM patients").fetchall()
    
    patient_id_map = {} # Maps SQLite ID to Supabase ID
    
    for row in rows:
        data = dict(row)
        sqlite_id = data.pop('id')
        data['is_clinic_patient'] = True
        
        res = supabase.table('patients').insert(data).execute()
        if res.data:
            patient_id_map[sqlite_id] = res.data[0]['id']
            
    print(f"Clinic patients migrated: {len(rows)}")
    return patient_id_map

def migrate_surgical_cases(patient_id_map):
    print("migrating surgical logbook cases...")
    conn = get_surgery_conn()
    if not conn: return
    rows = conn.execute("SELECT * FROM cases").fetchall()
    
    for row in rows:
        data = dict(row)
        case_id = data.pop('id')
        
        # We need to map or create the patient. 
        # In surgical logbook, we only have patient_name, mrn, age, gender.
        name = data.pop('patient_name')
        mrn = data.pop('mrn', None)
        age = data.pop('age', None)
        gender = data.pop('gender', None)
        
        # Check if a patient with this name/MRN already exists in Supabase
        query = supabase.table('patients').select('id').eq('name', name)
        if mrn:
            query = query.eq('mrn', mrn)
        
        existing_patient = query.execute()
        
        if existing_patient.data:
            supa_patient_id = existing_patient.data[0]['id']
        else:
            # Create a new patient (Fellowship/Surgery only)
            new_pt = {
                'name': name,
                'mrn': mrn,
                'age': age,
                'gender': gender,
                'is_clinic_patient': False
            }
            res = supabase.table('patients').insert(new_pt).execute()
            supa_patient_id = res.data[0]['id'] if res.data else None
            
        if supa_patient_id:
            data['patient_id'] = supa_patient_id
            res = supabase.table('surgical_cases').insert(data).execute()
            
            # Migrate followups for this case
            if res.data:
                supa_case_id = res.data[0]['id']
                fu_rows = conn.execute("SELECT * FROM followups WHERE case_id=?", (case_id,)).fetchall()
                for fu in fu_rows:
                    fu_data = dict(fu)
                    fu_data.pop('id')
                    fu_data['case_id'] = supa_case_id
                    supabase.table('surgical_followups').insert(fu_data).execute()
                    
    print(f"Surgical logbook cases and followups migrated.")

def main():
    print("--- Starting Migration ---")
    migrate_users()
    migrate_hospitals()
    patient_map = migrate_patients()
    migrate_surgical_cases(patient_map)
    # The rest of the tables (visits, invoices, etc) can be migrated similarly.
    # For now, this handles the core unified tables.
    print("--- Migration Script Finished ---")

if __name__ == "__main__":
    main()
