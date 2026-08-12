"""
clinic_db.py — Database connection, initialization, and core helpers for Orthopedic Clinic
Refactored for Supabase REST Client
"""
from core.database import get_supabase, hash_password, verify_password
from datetime import date, timedelta

# ----------------- Patients -----------------

def get_all_patients(search=""):
    """Returns ALL patients (clinic + logbook) for the combined patient list."""
    supabase = get_supabase()
    if search:
        q = f"%{search}%"
        response = supabase.table('patients').select('*').or_(f"name.ilike.{q},phone.ilike.{q},insurance.ilike.{q}").order('name').execute()
    else:
        response = supabase.table('patients').select('*').order('name').execute()
    return response.data

def get_clinic_patients(search=""):
    """Returns only clinic patients (is_clinic_patient=True) for statistics."""
    supabase = get_supabase()
    if search:
        q = f"%{search}%"
        response = supabase.table('patients').select('*').eq('is_clinic_patient', True).or_(f"name.ilike.{q},phone.ilike.{q},insurance.ilike.{q}").order('name').execute()
    else:
        response = supabase.table('patients').select('*').eq('is_clinic_patient', True).order('name').execute()
    return response.data

def get_patient(pid):
    supabase = get_supabase()
    response = supabase.table('patients').select('*').eq('id', pid).execute()
    return response.data[0] if response.data else None

def save_patient(data, pid=None):
    supabase = get_supabase()
    fields = [
        "name","dob","phone","insurance","is_insured","dm","htn","asthma","medications",
        "allergies","surgeries","notes","occupation","sports_level",
        "smoking","injury_mechanism","laterality","chronic_diseases",
        "insurance_policy_no","insurance_expiry","emergency_contact"
    ]
    payload = {f: data.get(f, "") for f in fields}
    
    if pid:
        supabase.table('patients').update(payload).eq('id', pid).execute()
        return pid
    else:
        response = supabase.table('patients').insert(payload).execute()
        if response.data:
            return response.data[0]['id']
        return None

def delete_patient(pid):
    supabase = get_supabase()
    supabase.table('patients').delete().eq('id', pid).execute()

def set_clinic_patient(pid, is_clinic=True):
    """Toggle whether a patient is a clinic patient or logbook-only."""
    supabase = get_supabase()
    supabase.table('patients').update({'is_clinic_patient': is_clinic}).eq('id', pid).execute()

# ----------------- Visits -----------------

def get_visits(patient_id):
    supabase = get_supabase()
    response = supabase.table('visits').select('*').eq('patient_id', patient_id).order('visit_date', desc=True).execute()
    return response.data

def get_visit(vid):
    supabase = get_supabase()
    response = supabase.table('visits').select('*').eq('id', vid).execute()
    return response.data[0] if response.data else None

def save_visit(data, vid=None):
    supabase = get_supabase()
    fields = [
        "patient_id","visit_date","reason","history","examination","labs",
        "xray","ct","mri","us","imaging_other",
        "diagnosis","medications","procedures","followup","referrals",
        "template_used", "rom_notes", "special_tests", "neurovascular", "injury_mechanism"
    ]
    payload = {f: data.get(f, "") for f in fields}
    
    if vid:
        supabase.table('visits').update(payload).eq('id', vid).execute()
        return vid
    else:
        response = supabase.table('visits').insert(payload).execute()
        if response.data:
            return response.data[0]['id']
        return None

def delete_visit(vid):
    supabase = get_supabase()
    supabase.table('visits').delete().eq('id', vid).execute()

# ----------------- Procedures Log -----------------

def get_procedures_log(patient_id):
    supabase = get_supabase()
    response = supabase.table('procedures_log').select('*').eq('patient_id', patient_id).order('procedure_date', desc=True).execute()
    return response.data

def add_procedure_log(data):
    supabase = get_supabase()
    response = supabase.table('procedures_log').insert(data).execute()
    return response.data[0]['id'] if response.data else None

def delete_procedure_log(proc_id):
    supabase = get_supabase()
    supabase.table('procedures_log').delete().eq('id', proc_id).execute()

def get_distinct_procedure_types():
    supabase = get_supabase()
    response = supabase.table('procedures_log').select('procedure_type').neq('procedure_type', 'Other').execute()
    types = set(r['procedure_type'] for r in response.data if r.get('procedure_type'))
    return list(types)

def get_visit_procedures(visit_id):
    supabase = get_supabase()
    response = supabase.table('procedures_log').select('procedure_type, notes').eq('visit_id', visit_id).execute()
    return response.data

def delete_visit_procedures(visit_id):
    supabase = get_supabase()
    supabase.table('procedures_log').delete().eq('visit_id', visit_id).execute()

# ----------------- Surgeries -----------------

def get_surgeries(patient_id):
    supabase = get_supabase()
    response = supabase.table('surgeries').select('*').eq('patient_id', patient_id).order('surgery_date', desc=True).execute()
    return response.data

def add_surgery(data):
    supabase = get_supabase()
    response = supabase.table('surgeries').insert(data).execute()
    return response.data[0]['id'] if response.data else None

def delete_surgery(sid):
    supabase = get_supabase()
    supabase.table('surgeries').delete().eq('id', sid).execute()

def add_expense(data):
    supabase = get_supabase()
    response = supabase.table('expenses').insert(data).execute()
    return response.data[0]['id'] if response.data else None

def get_recent_expenses(limit=10):
    supabase = get_supabase()
    response = supabase.table('expenses').select('*').order('expense_date', desc=True).limit(limit).execute()
    return response.data

def get_expenses_in_range(start_date, end_date):
    supabase = get_supabase()
    response = supabase.table('expenses').select('amount').gte('expense_date', start_date).lte('expense_date', end_date).execute()
    return sum(r.get('amount', 0) for r in response.data)

def add_external_income(data):
    supabase = get_supabase()
    response = supabase.table('external_income').insert(data).execute()
    return response.data[0]['id'] if response.data else None

def get_recent_external_income(limit=10):
    supabase = get_supabase()
    response = supabase.table('external_income').select('*').order('income_date', desc=True).limit(limit).execute()
    return response.data

def get_external_income_in_range(start_date, end_date):
    supabase = get_supabase()
    response = supabase.table('external_income').select('amount').gte('income_date', start_date).lte('income_date', end_date).execute()
    return sum(r.get('amount', 0) for r in response.data)

def get_payments_in_range(start_date, end_date):
    supabase = get_supabase()
    response = supabase.table('payments').select('amount').gte('payment_date', start_date).lte('payment_date', end_date).execute()
    return sum(r.get('amount', 0) for r in response.data)

def get_unpaid_invoices():
    supabase = get_supabase()
    response = supabase.table('billing_invoices').select('*, patients(name), payments(amount)').neq('status', 'Paid').execute()
    invoices = []
    for inv in response.data:
        patient = inv.pop('patients', {}) or {}
        inv['name'] = patient.get('name', 'Unknown')
        payments = inv.pop('payments', [])
        inv['paid'] = sum(p.get('amount', 0) for p in payments) if payments else 0
        invoices.append(inv)
    return invoices

def get_invoices_in_range(start_date, end_date):
    supabase = get_supabase()
    response = supabase.table('billing_invoices').select('*, patients(name), payments(amount)').gte('invoice_date', start_date).lte('invoice_date', end_date).order('invoice_date', desc=True).execute()
    invoices = []
    for inv in response.data:
        patient = inv.pop('patients', {}) or {}
        inv['patient'] = patient.get('name', 'Unknown')
        payments = inv.pop('payments', [])
        inv['paid'] = sum(p.get('amount', 0) for p in payments) if payments else 0
        invoices.append(inv)
    return invoices

def add_billing_item(data):
    supabase = get_supabase()
    supabase.table('billing_items').insert(data).execute()

def update_invoice_status(inv_id, status):
    supabase = get_supabase()
    supabase.table('billing_invoices').update({'status': status}).eq('id', inv_id).execute()

def get_all_procedures_log():
    supabase = get_supabase()
    response = supabase.table('procedures_log').select('*, patients(name)').order('procedure_date', desc=True).limit(50).execute()
    results = []
    for row in response.data:
        patient = row.pop('patients', {}) or {}
        row['patient'] = patient.get('name', 'Unknown')
        results.append(row)
    return results

def get_outstanding_balance():
    supabase = get_supabase()
    invoices = get_unpaid_invoices()
    return sum(inv.get('net_amount', 0) - inv.get('paid', 0) for inv in invoices)

def get_all_visits():
    supabase = get_supabase()
    response = supabase.table('visits').select('*, patients(name)').order('visit_date', desc=True).execute()
    visits = []
    for row in response.data:
        patient = row.pop('patients', {}) or {}
        row['patient_name'] = patient.get('name', 'Unknown')
        visits.append(row)
    return visits

def get_all_surgeries():
    supabase = get_supabase()
    response = supabase.table('surgeries').select('*, patients(name)').order('surgery_date', desc=True).execute()
    surgeries = []
    for row in response.data:
        patient = row.pop('patients', {}) or {}
        row['patient_name'] = patient.get('name', 'Unknown')
        surgeries.append(row)
    return surgeries

def get_all_expenses():
    supabase = get_supabase()
    response = supabase.table('expenses').select('*').execute()
    return response.data

def get_all_payments():
    supabase = get_supabase()
    response = supabase.table('payments').select('*').execute()
    return response.data

# ----------------- Followups -----------------

def get_followups(patient_id):
    supabase = get_supabase()
    response = supabase.table('clinic_followups').select('*').eq('patient_id', patient_id).order('due_date', desc=True).execute()
    return response.data

def add_followup(data):
    supabase = get_supabase()
    response = supabase.table('clinic_followups').insert(data).execute()
    return response.data[0]['id'] if response.data else None

def update_followup_status(f_id, status):
    supabase = get_supabase()
    supabase.table('clinic_followups').update({'status': status}).eq('id', f_id).execute()

def get_upcoming_followups(days=7):
    supabase = get_supabase()
    today_str = str(date.today())
    future_str = str(date.today() + timedelta(days=days))
    
    response = (supabase.table('clinic_followups')
                .select('id, due_date, rehab_phase, status, notes, patients(id, name)')
                .eq('status', 'Pending')
                .gte('due_date', today_str)
                .lte('due_date', future_str)
                .order('due_date')
                .execute())
    
    results = []
    for row in response.data:
        patient = row.pop('patients', {})
        if patient:
            row['patient_id'] = patient.get('id')
            row['patient_name'] = patient.get('name')
        results.append(row)
    return results

# ----------------- Appointments -----------------

def get_appointments(date_str):
    supabase = get_supabase()
    response = supabase.table('appointments').select('*, patients(id, name, phone)').eq('appointment_date', date_str).order('appointment_time').execute()
    results = []
    for row in response.data:
        patient = row.pop('patients', {}) or {}
        row['patient_name'] = patient.get('name', 'Unknown')
        row['patient_phone'] = patient.get('phone', '')
        row['patient_id'] = patient.get('id')
        results.append(row)
    return results

def get_all_appointments():
    supabase = get_supabase()
    response = supabase.table('appointments').select('*, patients(id, name, phone)').order('appointment_date', desc=True).execute()
    results = []
    for row in response.data:
        patient = row.pop('patients', {}) or {}
        row['patient_name'] = patient.get('name', 'Unknown')
        row['patient_phone'] = patient.get('phone', '')
        row['patient_id'] = patient.get('id')
        results.append(row)
    return results

def add_appointment(data):
    supabase = get_supabase()
    response = supabase.table('appointments').insert(data).execute()
    return response.data[0]['id'] if response.data else None

def delete_appointment(apt_id):
    supabase = get_supabase()
    supabase.table('appointments').delete().eq('id', apt_id).execute()

def update_appointment_status(apt_id, new_status):
    supabase = get_supabase()
    supabase.table('appointments').update({'status': new_status}).eq('id', apt_id).execute()

def get_today_appointment_count():
    supabase = get_supabase()
    today = str(date.today())
    response = supabase.table('appointments').select('id', count='exact').eq('appointment_date', today).execute()
    return response.count if hasattr(response, 'count') and response.count is not None else 0

# ----------------- Billing / Invoices -----------------

def get_patient_invoices(patient_id):
    supabase = get_supabase()
    response = supabase.table('billing_invoices').select('*, payments(amount)').eq('patient_id', patient_id).order('invoice_date', desc=True).execute()
    invoices = response.data
    for inv in invoices:
        payments = inv.pop('payments', [])
        if payments:
            inv['paid'] = sum(p.get('amount', 0) for p in payments)
        else:
            inv['paid'] = 0
    return invoices

def create_invoice(data):
    supabase = get_supabase()
    response = supabase.table('billing_invoices').insert(data).execute()
    return response.data[0]['id'] if response.data else None

def add_payment(data):
    supabase = get_supabase()
    response = supabase.table('payments').insert(data).execute()
    return response.data[0]['id'] if response.data else None

def create_billing_item(data):
    supabase = get_supabase()
    response = supabase.table('billing_items').insert(data).execute()
    return response.data[0]['id'] if response.data else None

def get_invoice(inv_id):
    supabase = get_supabase()
    response = supabase.table('billing_invoices').select('*, payments(*)').eq('id', inv_id).execute()
    if not response.data:
        return None
    inv = response.data[0]
    inv['paid'] = sum(p.get('amount', 0) for p in inv.get('payments', []))
    return inv

def get_all_invoices():
    supabase = get_supabase()
    response = supabase.table('billing_invoices').select('*, patients(name), payments(amount)').order('invoice_date', desc=True).execute()
    invoices = []
    for inv in response.data:
        patient = inv.pop('patients', {}) or {}
        inv['patient_name'] = patient.get('name', 'Unknown')
        payments = inv.pop('payments', [])
        inv['paid'] = sum(p.get('amount', 0) for p in payments) if payments else 0
        invoices.append(inv)
    return invoices

def get_revenue_summary():
    supabase = get_supabase()
    invoices = supabase.table('billing_invoices').select('total_amount').execute().data
    payments = supabase.table('payments').select('amount').execute().data
    total_invoiced = sum(i.get('total_amount', 0) or 0 for i in invoices)
    total_paid = sum(p.get('amount', 0) or 0 for p in payments)
    return {
        'total_invoiced': total_invoiced,
        'total_paid': total_paid,
        'outstanding': total_invoiced - total_paid
    }

# ----------------- Inventory -----------------

def get_all_inventory():
    supabase = get_supabase()
    response = supabase.table('inventory').select('*').order('item_name').execute()
    return response.data

def add_inventory_item(data):
    supabase = get_supabase()
    response = supabase.table('inventory').insert(data).execute()
    return response.data[0]['id'] if response.data else None

def update_inventory_item(item_id, data):
    supabase = get_supabase()
    supabase.table('inventory').update(data).eq('id', item_id).execute()

def delete_inventory_item(item_id):
    supabase = get_supabase()
    supabase.table('inventory').delete().eq('id', item_id).execute()

def get_low_stock_items():
    supabase = get_supabase()
    response = supabase.table('inventory').select('*').execute()
    return [item for item in response.data if (item.get('current_stock') or 0) <= (item.get('min_stock_alert') or 0)]

# ----------------- Analytics -----------------

def get_dashboard_stats():
    supabase = get_supabase()
    
    # Count only clinic patients for dashboard stats
    pt_resp = supabase.table('patients').select('id', count='exact').eq('is_clinic_patient', True).execute()
    total_patients = pt_resp.count if hasattr(pt_resp, 'count') and pt_resp.count is not None else 0

    v_resp = supabase.table('visits').select('id', count='exact').execute()
    total_visits = v_resp.count if hasattr(v_resp, 'count') and v_resp.count is not None else 0
    
    today_appointments = get_today_appointment_count()
    upcoming_followups = len(get_upcoming_followups(7))
    rev = get_revenue_summary()

    recent_v_resp = supabase.table('visits').select('*, patients(name)').order('visit_date', desc=True).limit(5).execute()
    recent_visits = []
    for v in recent_v_resp.data:
        p = v.pop('patients', {}) or {}
        v['patient_name'] = p.get('name', 'Unknown')
        recent_visits.append(v)

    return {
        'total_patients': total_patients,
        'total_visits': total_visits,
        'today_appointments': today_appointments,
        'upcoming_followups': upcoming_followups,
        'revenue': rev,
        'recent_visits': recent_visits
    }

# ----------------- Admin / Users -----------------

def get_all_users():
    supabase = get_supabase()
    response = supabase.table('users').select('id, username, role, created_at').order('username').execute()
    return response.data

def add_user(data):
    supabase = get_supabase()
    raw_password = data.pop('password', '')
    if raw_password:
        data['password_hash'] = hash_password(raw_password)
    response = supabase.table('users').insert(data).execute()
    return response.data[0]['id'] if response.data else None

def delete_user(user_id):
    supabase = get_supabase()
    supabase.table('users').delete().eq('id', user_id).execute()

def change_user_password(user_id, new_password):
    supabase = get_supabase()
    pwd_hash = hash_password(new_password)
    supabase.table('users').update({'password_hash': pwd_hash}).eq('id', user_id).execute()

# ----------------- Master Search -----------------

def master_search(query):
    supabase = get_supabase()
    q = f"%{query}%"
    
    # 1. Find matching patients
    pt_or_cond = f"name.ilike.{q},phone.ilike.{q},insurance.ilike.{q}"
    pt_response = supabase.table('patients').select('id, name, dob, phone, insurance').or_(pt_or_cond).execute()
    matched_patients_dict = {p['id']: p for p in pt_response.data}
    
    # 2. Find visits matching the query directly
    v_or_cond = (
        f"diagnosis.ilike.{q},medications.ilike.{q},procedures.ilike.{q},"
        f"history.ilike.{q},examination.ilike.{q},labs.ilike.{q},"
        f"xray.ilike.{q},ct.ilike.{q},mri.ilike.{q},us.ilike.{q},"
        f"imaging_other.ilike.{q},reason.ilike.{q},"
        f"followup.ilike.{q},referrals.ilike.{q}"
    )
    v_response = supabase.table('visits').select('*, patients(id, name, dob, phone, insurance)').or_(v_or_cond).order('visit_date', desc=True).execute()
    
    # 3. Find visits for matching patients that might not match the text query
    extra_visits = []
    if matched_patients_dict:
        extra_v_response = supabase.table('visits').select('*, patients(id, name, dob, phone, insurance)').in_('patient_id', list(matched_patients_dict.keys())).order('visit_date', desc=True).execute()
        extra_visits = extra_v_response.data
        
    # Combine and deduplicate
    all_visits = {v['id']: v for v in v_response.data}
    for v in extra_visits:
        if v['id'] not in all_visits:
            all_visits[v['id']] = v
            
    # Sort by visit date descending
    sorted_visits = sorted(all_visits.values(), key=lambda x: x.get('visit_date') or "", reverse=True)
    
    results = []
    for v in sorted_visits:
        p = v.get('patients') or {}
        res = {
            'patient_id': p.get('id'),
            'patient_name': p.get('name'),
            'dob': p.get('dob'),
            'phone': p.get('phone'),
            'insurance': p.get('insurance'),
            'visit_id': v.get('id'),
            'visit_date': v.get('visit_date'),
            'reason': v.get('reason'),
            'diagnosis': v.get('diagnosis'),
            'treatment_meds': v.get('medications'),
            'procedures': v.get('procedures'),
            'history': v.get('history'),
            'examination': v.get('examination'),
            'labs': v.get('labs'),
            'xray': v.get('xray'),
            'ct': v.get('ct'),
            'mri': v.get('mri'),
            'us': v.get('us'),
            'imaging_other': v.get('imaging_other'),
            'followup': v.get('followup'),
            'referrals': v.get('referrals')
        }
        results.append(res)
        
    return results

