
import sqlite3
from pathlib import Path
from datetime import date, timedelta, datetime
import pandas as pd
import streamlit as st

DB_PATH = Path("stableflow.db")

PROGRAMS = ["Agistment", "Spelling", "Pre-Training", "Race Training", "Rehab", "Breaking-In", "Let-Down"]
MEAL_TIMES = ["AM", "Midday", "PM", "Night"]
UNITS = ["kg", "g", "ml", "scoop", "biscuit", "flake", "tablet", "dose"]
TASKS = ["Feeding", "Maintenance", "Medical", "Training", "Admin", "Transfer", "Treatment", "Raceday"]
ROUTES = ["Oral", "Injection", "Topical", "In feed", "IV", "IM", "SC", "Other"]

st.set_page_config(page_title="StableFlow", page_icon="🐎", layout="wide")

st.markdown("""
<style>
.block-container{padding-top:1.3rem;}
.sf-hero{background:linear-gradient(135deg,#1F2937,#0F172A);border:1px solid rgba(200,155,60,.45);padding:24px;border-radius:22px;margin-bottom:20px;}
.sf-title{font-size:38px;font-weight:800;color:#F9FAFB;margin-bottom:4px;}
.sf-gold{color:#C89B3C;}
.sf-subtitle{color:#CBD5E1;font-size:17px;}
.sf-pill{display:inline-block;padding:4px 10px;border-radius:999px;background:rgba(200,155,60,.15);color:#F6E7B7;border:1px solid rgba(200,155,60,.35);font-size:12px;}
div[data-testid="stMetricValue"]{color:#F9FAFB;}
div[data-testid="stMetricLabel"]{color:#CBD5E1;}
</style>
""", unsafe_allow_html=True)

def conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init():
    c = conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS owners(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, phone TEXT, email TEXT, notes TEXT
    );

    CREATE TABLE IF NOT EXISTS properties(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, location TEXT, notes TEXT
    );

    CREATE TABLE IF NOT EXISTS horses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, breed TEXT, owner_id INTEGER, trainer TEXT, property_id INTEGER,
        program TEXT, status TEXT, notes TEXT
    );

    CREATE TABLE IF NOT EXISTS program_rates(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        program TEXT UNIQUE,
        base_day_rate REAL,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS feed_ingredients(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        default_unit TEXT,
        cost_per_unit REAL,
        billable INTEGER DEFAULT 0,
        bill_price_per_unit REAL DEFAULT 0,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS feed_programs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        program_type TEXT,
        notes TEXT,
        active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS feed_program_meals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feed_program_id INTEGER,
        meal_time TEXT,
        prep_notes TEXT
    );

    CREATE TABLE IF NOT EXISTS feed_program_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        program_meal_id INTEGER,
        ingredient_id INTEGER,
        quantity REAL,
        unit TEXT,
        is_supplement INTEGER DEFAULT 0,
        is_medication INTEGER DEFAULT 0,
        billable INTEGER DEFAULT 0,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS horse_feed_assignments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        horse_id INTEGER,
        feed_program_id INTEGER,
        start_date TEXT,
        end_date TEXT,
        status TEXT,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS feed_overrides(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        horse_id INTEGER,
        ingredient_id INTEGER,
        adjustment_type TEXT,
        quantity REAL,
        unit TEXT,
        start_date TEXT,
        end_date TEXT,
        reason TEXT,
        billable INTEGER DEFAULT 0,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, horse_id INTEGER, assigned_to TEXT, category TEXT,
        due_date TEXT, status TEXT, notes TEXT
    );

    CREATE TABLE IF NOT EXISTS troughs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, property_id INTEGER, frequency TEXT, last_cleaned TEXT,
        next_due TEXT, staff TEXT, notes TEXT
    );

    CREATE TABLE IF NOT EXISTS medical(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        horse_id INTEGER, record_date TEXT, vet TEXT, issue TEXT, treatment TEXT,
        follow_up TEXT, status TEXT, notes TEXT
    );

    CREATE TABLE IF NOT EXISTS treatment_log(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        horse_id INTEGER,
        treatment_date TEXT,
        treatment_time TEXT,
        treatment_type TEXT,
        product_name TEXT,
        dose TEXT,
        route TEXT,
        reason TEXT,
        administered_by TEXT,
        vet_authority TEXT,
        withholding_days INTEGER DEFAULT 0,
        eligible_to_race_date TEXT,
        billable INTEGER DEFAULT 1,
        charge_amount REAL DEFAULT 0,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS training(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        horse_id INTEGER, trainer TEXT, type TEXT, session_date TEXT,
        distance INTEGER, time TEXT, rating INTEGER, notes TEXT
    );

    CREATE TABLE IF NOT EXISTS transfers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        horse_id INTEGER, from_property TEXT, to_property TEXT,
        transfer_date TEXT, program TEXT, notes TEXT
    );

    CREATE TABLE IF NOT EXISTS chargeable_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        unit_type TEXT,
        default_price REAL,
        active INTEGER DEFAULT 1,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS horse_charges(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        horse_id INTEGER,
        charge_item_id INTEGER,
        start_date TEXT,
        end_date TEXT,
        quantity REAL,
        frequency TEXT,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS raceday_charges(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        horse_id INTEGER,
        race_date TEXT,
        racecourse TEXT,
        charge_name TEXT,
        category TEXT,
        amount REAL,
        billable INTEGER DEFAULT 1,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS race_results(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        horse_id INTEGER,
        race_date TEXT,
        racecourse TEXT,
        race_number TEXT,
        race_name TEXT,
        distance_m INTEGER,
        barrier TEXT,
        jockey TEXT,
        weight TEXT,
        track_condition TEXT,
        result_position TEXT,
        margin TEXT,
        prize_money REAL DEFAULT 0,
        trainer_comments TEXT,
        jockey_comments TEXT,
        recovery_notes TEXT,
        next_plan TEXT,
        owner_update TEXT,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS invoices(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER,
        invoice_date TEXT,
        period_start TEXT,
        period_end TEXT,
        amount REAL,
        status TEXT,
        due_date TEXT,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS invoice_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER,
        horse_id INTEGER,
        description TEXT,
        quantity REAL,
        unit_price REAL,
        line_total REAL
    );
    """)
    c.commit()
    c.close()

def q(sql, params=()):
    c = conn()
    df = pd.read_sql_query(sql, c, params=params)
    c.close()
    return df

def x(sql, params=()):
    c = conn()
    c.execute(sql, params)
    c.commit()
    c.close()

def opts(table, label="name"):
    df = q(f"SELECT id,{label} FROM {table} ORDER BY {label}")
    return {f"{r[label]} · #{r['id']}": int(r["id"]) for _, r in df.iterrows()}

def days_overlap(start1, end1, start2, end2):
    s1 = date.fromisoformat(start1)
    e1 = date.fromisoformat(end1)
    s2 = date.fromisoformat(start2)
    e2 = date.fromisoformat(end2)
    start = max(s1, s2)
    end = min(e1, e2)
    return max(0, (end - start).days + 1)

def sample():
    if not q("SELECT * FROM owners").empty:
        return

    x("INSERT INTO owners(name,phone,email,notes) VALUES(?,?,?,?)",("Topform Syndicate","0400 000 001","syndicate@example.com","Racehorse owners"))
    x("INSERT INTO owners(name,phone,email,notes) VALUES(?,?,?,?)",("Sarah Smith","0400 000 002","sarah@example.com","Spelling client"))
    x("INSERT INTO properties(name,location,notes) VALUES(?,?,?)",("Topform Lodge","North Dandalup","Main property"))
    x("INSERT INTO properties(name,location,notes) VALUES(?,?,?)",("Topform Spelling","Pinjarra","Spelling farm"))

    for program, rate in [("Agistment",35),("Spelling",45),("Pre-Training",85),("Race Training",120),("Rehab",70),("Let-Down",55)]:
        x("INSERT INTO program_rates(program,base_day_rate,notes) VALUES(?,?,?)",(program, rate, "Sample rate"))

    x("INSERT INTO horses(name,breed,owner_id,trainer,property_id,program,status,notes) VALUES(?,?,?,?,?,?,?,?)",("Topform Star","Thoroughbred",1,"J. Trainer",1,"Race Training","Active","Main sample racehorse"))
    x("INSERT INTO horses(name,breed,owner_id,trainer,property_id,program,status,notes) VALUES(?,?,?,?,?,?,?,?)",("Daisy","Thoroughbred",2,"J. Trainer",2,"Spelling","Active","Sample spelling horse"))

    ingredients = [
        ("Lucerne Chaff","Chaff","kg",1.70,0,0,""),
        ("Performance Pellets","Pellets","kg",1.52,0,0,""),
        ("Oaten Hay","Hay","biscuit",4.00,0,0,""),
        ("Electrolytes","Supplement","g",0.20,1,2.00,"Bill daily when added"),
        ("Joint Supplement","Supplement","scoop",2.50,1,2.50,""),
        ("Ulcer Medication","Medication","dose",12.00,1,12.00,"")
    ]
    for item in ingredients:
        x("INSERT INTO feed_ingredients(name,category,default_unit,cost_per_unit,billable,bill_price_per_unit,notes) VALUES(?,?,?,?,?,?,?)", item)

    x("INSERT INTO feed_programs(name,program_type,notes,active) VALUES(?,?,?,?)",("Racehorse Base Feed","Race Training","Standard racehorse feed",1))
    x("INSERT INTO feed_programs(name,program_type,notes,active) VALUES(?,?,?,?)",("Spelling Base Feed","Spelling","Standard spelling feed",1))
    x("INSERT INTO feed_program_meals(feed_program_id,meal_time,prep_notes) VALUES(?,?,?)",(1,"AM","Feed dry."))
    x("INSERT INTO feed_program_meals(feed_program_id,meal_time,prep_notes) VALUES(?,?,?)",(1,"PM","Add hay separately."))
    x("INSERT INTO feed_program_items(program_meal_id,ingredient_id,quantity,unit,is_supplement,is_medication,billable,notes) VALUES(?,?,?,?,?,?,?,?)",(1,1,2,"kg",0,0,0,""))
    x("INSERT INTO feed_program_items(program_meal_id,ingredient_id,quantity,unit,is_supplement,is_medication,billable,notes) VALUES(?,?,?,?,?,?,?,?)",(1,2,1.5,"kg",0,0,0,""))
    x("INSERT INTO feed_program_items(program_meal_id,ingredient_id,quantity,unit,is_supplement,is_medication,billable,notes) VALUES(?,?,?,?,?,?,?,?)",(2,2,1,"kg",0,0,0,""))
    x("INSERT INTO feed_program_items(program_meal_id,ingredient_id,quantity,unit,is_supplement,is_medication,billable,notes) VALUES(?,?,?,?,?,?,?,?)",(2,3,1,"biscuit",0,0,0,""))

    today = str(date.today())
    x("INSERT INTO horse_feed_assignments(horse_id,feed_program_id,start_date,end_date,status,notes) VALUES(?,?,?,?,?,?)",(1,1,today,"","Active",""))
    x("INSERT INTO feed_overrides(horse_id,ingredient_id,adjustment_type,quantity,unit,start_date,end_date,reason,billable,notes) VALUES(?,?,?,?,?,?,?,?,?,?)",(1,4,"Add",30,"g",today,str(date.today()+timedelta(days=5)),"Race lead-up",1,"Add electrolytes"))

    x("INSERT INTO tasks(name,horse_id,assigned_to,category,due_date,status,notes) VALUES(?,?,?,?,?,?,?)",("AM feed round",1,"Staff","Feeding",today,"Not Started","Sample"))
    x("INSERT INTO troughs(name,property_id,frequency,last_cleaned,next_due,staff,notes) VALUES(?,?,?,?,?,?,?)",("Trough 1",1,"Weekly",str(date.today()-timedelta(days=8)),str(date.today()-timedelta(days=1)),"Staff","Due"))
    x("INSERT INTO medical(horse_id,record_date,vet,issue,treatment,follow_up,status,notes) VALUES(?,?,?,?,?,?,?,?)",(1,today,"Dr Smith","Mild soreness","Rest + ice",str(date.today()+timedelta(days=7)),"Open","Sample"))

    x("""INSERT INTO treatment_log(horse_id,treatment_date,treatment_time,treatment_type,product_name,dose,route,reason,administered_by,vet_authority,withholding_days,eligible_to_race_date,billable,charge_amount,notes)
       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      (1,today,"07:00","Medication","Ulcer Medication","1 dose","Oral","Race prep","Staff","Dr Smith instruction",7,str(date.today()+timedelta(days=7)),1,12.00,"Sample treatment record"))

    x("INSERT INTO chargeable_items(name,category,unit_type,default_price,active,notes) VALUES(?,?,?,?,?,?)",("Ulcer Medication","Medication","day",12.00,1,""))
    x("INSERT INTO chargeable_items(name,category,unit_type,default_price,active,notes) VALUES(?,?,?,?,?,?)",("Raceday Fee","Raceday","event",150.00,1,"Standard raceday attendance/admin fee"))
    x("INSERT INTO horse_charges(horse_id,charge_item_id,start_date,end_date,quantity,frequency,notes) VALUES(?,?,?,?,?,?,?)",(1,1,today,str(date.today()+timedelta(days=6)),1,"Daily","Ulcer meds"))

    x("""INSERT INTO raceday_charges(horse_id,race_date,racecourse,charge_name,category,amount,billable,notes)
         VALUES(?,?,?,?,?,?,?,?)""",(1,today,"Belmont","Raceday Fee","Raceday",150,1,"Sample raceday charge"))
    x("""INSERT INTO race_results(horse_id,race_date,racecourse,race_number,race_name,distance_m,barrier,jockey,weight,track_condition,result_position,margin,prize_money,trainer_comments,jockey_comments,recovery_notes,next_plan,owner_update,notes)
         VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      (1,today,"Belmont","Race 6","Class 1 Handicap",1200,"4","J. Rider","58kg","Good 4","2nd","0.5L",8000,"Excellent run, finished strongly.","Settled well and hit line.","Pulled up bright.","Look for 1400m next start.","Great run today, very promising effort.","Sample result"))

def hero():
    st.markdown('<div class="sf-hero"><div class="sf-title">Stable<span class="sf-gold">Flow</span></div><div class="sf-subtitle">Feed templates, overrides, treatment register, race results, billing and horse lifecycle tracking.</div></div>', unsafe_allow_html=True)

def header(title, sub):
    st.markdown(f"## {title}")
    st.caption(sub)
    st.markdown("---")

def dashboard():
    hero()
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("🐎 Horses", int(q("SELECT COUNT(*) n FROM horses").iloc[0].n))
    c2.metric("🥕 Feed Programs", int(q("SELECT COUNT(*) n FROM feed_programs WHERE active=1").iloc[0].n))
    c3.metric("🏇 Race Results", int(q("SELECT COUNT(*) n FROM race_results").iloc[0].n))
    c4.metric("💊 Active Treatments", int(q("SELECT COUNT(*) n FROM treatment_log WHERE eligible_to_race_date >= ?",(str(date.today()),)).iloc[0].n))
    st.markdown("### Today’s Feed Sheet")
    st.dataframe(feed_sheet_df(), use_container_width=True, hide_index=True)
    st.markdown("### Recent Race Results")
    st.dataframe(q("""SELECT h.name Horse, rr.race_date Date, rr.racecourse Racecourse, rr.race_name Race, rr.result_position Result, rr.trainer_comments Comments
                      FROM race_results rr JOIN horses h ON rr.horse_id=h.id ORDER BY rr.race_date DESC LIMIT 5"""), use_container_width=True, hide_index=True)

def owners_page():
    header("Owners","Manage owners, syndicates and client contacts.")
    with st.expander("➕ Add owner"):
        with st.form("owner"):
            name=st.text_input("Name"); phone=st.text_input("Phone"); email=st.text_input("Email"); notes=st.text_area("Notes")
            if st.form_submit_button("Save owner"):
                x("INSERT INTO owners(name,phone,email,notes) VALUES(?,?,?,?)",(name,phone,email,notes)); st.success("Saved"); st.rerun()
    st.dataframe(q("SELECT id ID,name Name,phone Phone,email Email,notes Notes FROM owners ORDER BY name"),hide_index=True,use_container_width=True)

def horses_page():
    header("Horses","One horse record across agistment, spelling, pre-training, racing and rehab.")
    owners=opts("owners"); props=opts("properties")
    with st.expander("➕ Add horse"):
        with st.form("horse"):
            c1,c2=st.columns(2)
            name=c1.text_input("Horse name"); breed=c2.text_input("Breed")
            owner=c1.selectbox("Owner", list(owners.keys())) if owners else None
            prop=c2.selectbox("Property", list(props.keys())) if props else None
            trainer=c1.text_input("Trainer"); program=c2.selectbox("Program", PROGRAMS)
            status=c1.selectbox("Status",["Active","Inactive","On Hold","Completed"])
            notes=st.text_area("Notes")
            if st.form_submit_button("Save horse"):
                x("INSERT INTO horses(name,breed,owner_id,trainer,property_id,program,status,notes) VALUES(?,?,?,?,?,?,?,?)",(name,breed,owners.get(owner) if owner else None,trainer,props.get(prop) if prop else None,program,status,notes)); st.success("Saved"); st.rerun()
    st.dataframe(q("""SELECT h.id ID,h.name Horse,h.breed Breed,o.name Owner,h.trainer Trainer,p.name Property,h.program Program,h.status Status
                      FROM horses h LEFT JOIN owners o ON h.owner_id=o.id LEFT JOIN properties p ON h.property_id=p.id ORDER BY h.name"""),hide_index=True,use_container_width=True)

def feed_sheet_df():
    base = q("""
        SELECT h.id Horse_ID, h.name Horse, fp.name Feed_Program, fpm.meal_time Meal,
               GROUP_CONCAT(fi.name || ' - ' || fpi.quantity || ' ' || fpi.unit, CHAR(10)) Ingredients,
               fpm.prep_notes Prep_Notes
        FROM horse_feed_assignments hfa
        JOIN horses h ON hfa.horse_id=h.id
        JOIN feed_programs fp ON hfa.feed_program_id=fp.id
        JOIN feed_program_meals fpm ON fp.id=fpm.feed_program_id
        LEFT JOIN feed_program_items fpi ON fpm.id=fpi.program_meal_id
        LEFT JOIN feed_ingredients fi ON fpi.ingredient_id=fi.id
        WHERE hfa.status='Active'
        GROUP BY h.id, fpm.id
        ORDER BY h.name, CASE fpm.meal_time WHEN 'AM' THEN 1 WHEN 'Midday' THEN 2 WHEN 'PM' THEN 3 ELSE 4 END
    """)
    overrides = q("""
        SELECT h.id Horse_ID, GROUP_CONCAT(fo.adjustment_type || ' ' || fi.name || ' - ' || fo.quantity || ' ' || fo.unit || ' (' || fo.reason || ')', CHAR(10)) Today_Overrides
        FROM feed_overrides fo
        JOIN horses h ON fo.horse_id=h.id
        JOIN feed_ingredients fi ON fo.ingredient_id=fi.id
        WHERE date(?) BETWEEN date(fo.start_date) AND date(fo.end_date)
        GROUP BY h.id
    """, (str(date.today()),))
    if base.empty:
        return base
    return base.merge(overrides, how="left", on="Horse_ID").drop(columns=["Horse_ID"])

def feed_page():
    header("Feed","Standard feed programs plus horse-specific temporary overrides.")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Daily Feed Sheet", "Ingredients", "Feed Programs", "Assign Program", "Overrides"])

    with tab1:
        st.dataframe(feed_sheet_df(), use_container_width=True, hide_index=True)

    with tab2:
        with st.form("ingredient"):
            c1,c2=st.columns(2)
            name=c1.text_input("Ingredient name")
            category=c2.text_input("Category", placeholder="Chaff / Pellets / Supplement / Medication")
            unit=c1.selectbox("Default unit", UNITS)
            cost=c2.number_input("Cost per unit", min_value=0.0, value=0.0, step=0.10)
            billable=c1.checkbox("Billable to owner")
            bill_price=c2.number_input("Bill price per unit", min_value=0.0, value=0.0, step=0.10)
            notes=st.text_area("Notes")
            if st.form_submit_button("Save ingredient"):
                x("INSERT INTO feed_ingredients(name,category,default_unit,cost_per_unit,billable,bill_price_per_unit,notes) VALUES(?,?,?,?,?,?,?)",(name,category,unit,cost,1 if billable else 0,bill_price,notes))
                st.success("Saved"); st.rerun()
        st.dataframe(q("SELECT id ID,name Ingredient,category Category,default_unit Unit,cost_per_unit Cost,billable Billable,bill_price_per_unit Bill_Price,notes Notes FROM feed_ingredients ORDER BY name"), use_container_width=True, hide_index=True)

    with tab3:
        with st.expander("Create feed program"):
            with st.form("feedprogram"):
                name=st.text_input("Feed program name", placeholder="Racehorse Base Feed")
                ptype=st.selectbox("Program type", PROGRAMS)
                notes=st.text_area("Notes")
                if st.form_submit_button("Save program"):
                    x("INSERT INTO feed_programs(name,program_type,notes,active) VALUES(?,?,?,?)",(name,ptype,notes,1)); st.success("Saved"); st.rerun()

        programs=opts("feed_programs")
        ingredients=opts("feed_ingredients")
        with st.expander("Add meal + ingredient to feed program"):
            with st.form("programmealitem"):
                program=st.selectbox("Feed program", list(programs.keys())) if programs else None
                meal=st.selectbox("Meal", MEAL_TIMES)
                prep=st.text_area("Prep notes")
                ingredient=st.selectbox("Ingredient", list(ingredients.keys())) if ingredients else None
                qty=st.number_input("Quantity", min_value=0.0, value=1.0, step=0.1)
                unit=st.selectbox("Unit", UNITS)
                supp=st.checkbox("Supplement")
                med=st.checkbox("Medication")
                billable=st.checkbox("Billable")
                notes=st.text_area("Ingredient notes")
                if st.form_submit_button("Add to program"):
                    x("INSERT INTO feed_program_meals(feed_program_id,meal_time,prep_notes) VALUES(?,?,?)",(programs.get(program),meal,prep))
                    meal_id = int(q("SELECT last_insert_rowid() id").iloc[0].id)
                    x("INSERT INTO feed_program_items(program_meal_id,ingredient_id,quantity,unit,is_supplement,is_medication,billable,notes) VALUES(?,?,?,?,?,?,?,?)",(meal_id,ingredients.get(ingredient),qty,unit,1 if supp else 0,1 if med else 0,1 if billable else 0,notes))
                    st.success("Added"); st.rerun()

        st.dataframe(q("""
            SELECT fp.name Program, fpm.meal_time Meal, fi.name Ingredient, fpi.quantity Qty, fpi.unit Unit,
                   fpi.is_supplement Supplement, fpi.is_medication Medication, fpi.billable Billable, fpm.prep_notes Prep
            FROM feed_program_items fpi
            JOIN feed_program_meals fpm ON fpi.program_meal_id=fpm.id
            JOIN feed_programs fp ON fpm.feed_program_id=fp.id
            JOIN feed_ingredients fi ON fpi.ingredient_id=fi.id
            ORDER BY fp.name, fpm.meal_time
        """), use_container_width=True, hide_index=True)

    with tab4:
        horses=opts("horses"); programs=opts("feed_programs")
        with st.form("assign_feed"):
            horse=st.selectbox("Horse", list(horses.keys())) if horses else None
            program=st.selectbox("Feed program", list(programs.keys())) if programs else None
            start=st.date_input("Start date", date.today())
            end=st.text_input("End date optional", placeholder="YYYY-MM-DD or blank")
            notes=st.text_area("Notes")
            if st.form_submit_button("Assign feed program"):
                x("INSERT INTO horse_feed_assignments(horse_id,feed_program_id,start_date,end_date,status,notes) VALUES(?,?,?,?,?,?)",(horses.get(horse),programs.get(program),str(start),end,"Active",notes))
                st.success("Assigned"); st.rerun()
        st.dataframe(q("""
            SELECT h.name Horse, fp.name Feed_Program, hfa.start_date Start, hfa.end_date End, hfa.status Status, hfa.notes Notes
            FROM horse_feed_assignments hfa
            JOIN horses h ON hfa.horse_id=h.id
            JOIN feed_programs fp ON hfa.feed_program_id=fp.id
            ORDER BY h.name
        """), use_container_width=True, hide_index=True)

    with tab5:
        horses=opts("horses"); ingredients=opts("feed_ingredients")
        with st.form("override"):
            horse=st.selectbox("Horse", list(horses.keys())) if horses else None
            ingredient=st.selectbox("Ingredient", list(ingredients.keys())) if ingredients else None
            adj=st.selectbox("Adjustment type", ["Add","Reduce","Remove","Replace"])
            qty=st.number_input("Quantity", min_value=0.0, value=1.0, step=0.1)
            unit=st.selectbox("Unit", UNITS)
            c1,c2=st.columns(2)
            start=c1.date_input("Start", date.today())
            end=c2.date_input("End", date.today()+timedelta(days=7))
            reason=st.text_input("Reason", placeholder="Race lead-up / let-down / vet instruction")
            billable=st.checkbox("Bill this override")
            notes=st.text_area("Notes")
            if st.form_submit_button("Save override"):
                x("INSERT INTO feed_overrides(horse_id,ingredient_id,adjustment_type,quantity,unit,start_date,end_date,reason,billable,notes) VALUES(?,?,?,?,?,?,?,?,?,?)",(horses.get(horse),ingredients.get(ingredient),adj,qty,unit,str(start),str(end),reason,1 if billable else 0,notes))
                st.success("Override saved"); st.rerun()
        st.dataframe(q("""
            SELECT h.name Horse, fo.adjustment_type Type, fi.name Ingredient, fo.quantity Qty, fo.unit Unit,
                   fo.start_date Start, fo.end_date End, fo.reason Reason, fo.billable Billable, fo.notes Notes
            FROM feed_overrides fo
            JOIN horses h ON fo.horse_id=h.id
            JOIN feed_ingredients fi ON fo.ingredient_id=fi.id
            ORDER BY fo.start_date DESC
        """), use_container_width=True, hide_index=True)

def treatment_alerts_df():
    return q("""
        SELECT h.name Horse, tl.treatment_date Date, tl.product_name Product, tl.dose Dose,
               tl.route Route, tl.withholding_days Withholding_Days, tl.eligible_to_race_date Eligible_To_Race,
               CASE WHEN date(tl.eligible_to_race_date) > date(?) THEN 'WITHHOLDING ACTIVE' ELSE 'Clear/Expired' END Status
        FROM treatment_log tl
        JOIN horses h ON tl.horse_id=h.id
        ORDER BY tl.eligible_to_race_date DESC
    """,(str(date.today()),))

def treatments_page():
    header("Treatments","Licensed trainer treatment register with withholding and billing.")
    horses=opts("horses")
    tab1, tab2 = st.tabs(["Add Treatment", "Treatment Register"])

    with tab1:
        with st.form("treatment"):
            horse=st.selectbox("Horse", list(horses.keys())) if horses else None
            c1,c2,c3=st.columns(3)
            tdate=c1.date_input("Treatment date", date.today())
            ttime=c2.text_input("Time given", value=datetime.now().strftime("%H:%M"))
            ttype=c3.text_input("Treatment type", placeholder="Medication / Therapy / Supplement")
            product=st.text_input("Product / medication name")
            c4,c5,c6=st.columns(3)
            dose=c4.text_input("Dose / quantity")
            route=c5.selectbox("Route", ROUTES)
            withholding=c6.number_input("Withholding days", min_value=0, value=0, step=1)
            reason=st.text_area("Reason for treatment")
            administered=st.text_input("Administered by")
            vet_auth=st.text_input("Vet instruction / authority")
            billable=st.checkbox("Add to bill", value=True)
            charge=st.number_input("Charge amount", min_value=0.0, value=0.0, step=1.0)
            notes=st.text_area("Notes")
            if st.form_submit_button("Save Treatment Record"):
                eligible = tdate + timedelta(days=int(withholding))
                x("""INSERT INTO treatment_log(horse_id,treatment_date,treatment_time,treatment_type,product_name,dose,route,reason,administered_by,vet_authority,withholding_days,eligible_to_race_date,billable,charge_amount,notes)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (horses.get(horse),str(tdate),ttime,ttype,product,dose,route,reason,administered,vet_auth,int(withholding),str(eligible),1 if billable else 0,charge,notes))
                st.success("Treatment record saved")
                st.rerun()

    with tab2:
        st.markdown("### Treatment Register")
        st.dataframe(q("""
            SELECT tl.id ID, h.name Horse, tl.treatment_date Date, tl.treatment_time Time, tl.treatment_type Type,
                   tl.product_name Product, tl.dose Dose, tl.route Route, tl.reason Reason,
                   tl.administered_by "Given By", tl.vet_authority "Vet Authority",
                   tl.withholding_days Withholding, tl.eligible_to_race_date "Eligible To Race",
                   tl.billable Billable, tl.charge_amount Charge, tl.notes Notes
            FROM treatment_log tl
            JOIN horses h ON tl.horse_id=h.id
            ORDER BY tl.treatment_date DESC, tl.treatment_time DESC
        """), use_container_width=True, hide_index=True)

        st.markdown("### Withholding Alerts")
        st.dataframe(treatment_alerts_df(), use_container_width=True, hide_index=True)

def raceday_page():
    header("Raceday","Raceday charges, race results, comments and owner updates.")
    horses=opts("horses")
    tab1, tab2, tab3 = st.tabs(["Additional Raceday Charges", "Race Results", "Owner Update View"])

    with tab1:
        with st.form("raceday_charge"):
            horse=st.selectbox("Horse", list(horses.keys()), key="raceday_charge_horse") if horses else None
            c1,c2=st.columns(2)
            race_date=c1.date_input("Race date", date.today())
            racecourse=c2.text_input("Racecourse", placeholder="Belmont / Pinjarra / Ascot")
            charge_name=st.text_input("Charge name", placeholder="Raceday fee / Strapper fee / Transport / Race plates")
            category=st.selectbox("Category", ["Raceday", "Transport", "Farrier", "Staff", "Admin", "Gear", "Other"])
            amount=st.number_input("Amount", min_value=0.0, value=0.0, step=10.0)
            billable=st.checkbox("Bill to owner", value=True)
            notes=st.text_area("Notes")
            if st.form_submit_button("Save raceday charge"):
                x("""INSERT INTO raceday_charges(horse_id,race_date,racecourse,charge_name,category,amount,billable,notes)
                     VALUES(?,?,?,?,?,?,?,?)""",
                  (horses.get(horse),str(race_date),racecourse,charge_name,category,amount,1 if billable else 0,notes))
                st.success("Raceday charge saved")
                st.rerun()

        st.dataframe(q("""
            SELECT rc.id ID, h.name Horse, rc.race_date Date, rc.racecourse Racecourse, rc.charge_name Charge,
                   rc.category Category, rc.amount Amount, rc.billable Billable, rc.notes Notes
            FROM raceday_charges rc
            JOIN horses h ON rc.horse_id=h.id
            ORDER BY rc.race_date DESC
        """), use_container_width=True, hide_index=True)

    with tab2:
        with st.form("race_result"):
            horse=st.selectbox("Horse", list(horses.keys()), key="race_result_horse") if horses else None
            c1,c2,c3=st.columns(3)
            race_date=c1.date_input("Race date", date.today(), key="result_date")
            racecourse=c2.text_input("Racecourse", key="result_course")
            race_number=c3.text_input("Race number")
            race_name=st.text_input("Race name / grade")
            c4,c5,c6=st.columns(3)
            distance=c4.number_input("Distance (m)", min_value=0, value=1200, step=100)
            barrier=c5.text_input("Barrier")
            jockey=c6.text_input("Jockey")
            c7,c8,c9=st.columns(3)
            weight=c7.text_input("Weight")
            track=c8.text_input("Track condition")
            position=c9.text_input("Result / position", placeholder="1st / 2nd / 8th")
            margin=st.text_input("Margin")
            prize=st.number_input("Prize money", min_value=0.0, value=0.0, step=100.0)
            trainer_comments=st.text_area("Trainer comments")
            jockey_comments=st.text_area("Jockey comments")
            recovery_notes=st.text_area("Recovery / post-race notes")
            next_plan=st.text_area("Next plan")
            owner_update=st.text_area("Owner update summary")
            notes=st.text_area("Internal notes")
            if st.form_submit_button("Save race result"):
                x("""INSERT INTO race_results(horse_id,race_date,racecourse,race_number,race_name,distance_m,barrier,jockey,weight,track_condition,result_position,margin,prize_money,trainer_comments,jockey_comments,recovery_notes,next_plan,owner_update,notes)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (horses.get(horse),str(race_date),racecourse,race_number,race_name,int(distance),barrier,jockey,weight,track,position,margin,float(prize),trainer_comments,jockey_comments,recovery_notes,next_plan,owner_update,notes))
                st.success("Race result saved")
                st.rerun()

        st.dataframe(q("""
            SELECT rr.id ID, h.name Horse, rr.race_date Date, rr.racecourse Racecourse, rr.race_number Race_No,
                   rr.race_name Race, rr.distance_m Distance, rr.jockey Jockey, rr.result_position Result,
                   rr.margin Margin, rr.prize_money Prize, rr.trainer_comments Trainer_Comments, rr.next_plan Next_Plan
            FROM race_results rr
            JOIN horses h ON rr.horse_id=h.id
            ORDER BY rr.race_date DESC
        """), use_container_width=True, hide_index=True)

    with tab3:
        st.markdown("### Owner-friendly Race Updates")
        st.dataframe(q("""
            SELECT h.name Horse, rr.race_date Date, rr.racecourse Racecourse, rr.race_name Race,
                   rr.result_position Result, rr.owner_update Owner_Update, rr.next_plan Next_Plan
            FROM race_results rr
            JOIN horses h ON rr.horse_id=h.id
            ORDER BY rr.race_date DESC
        """), use_container_width=True, hide_index=True)

def tasks_page():
    header("Operations","Staff tasks and daily work.")
    horses=opts("horses")
    with st.expander("➕ Add task"):
        with st.form("task"):
            name=st.text_input("Task"); horse=st.selectbox("Horse",["None"]+list(horses.keys()))
            staff=st.text_input("Assigned to"); cat=st.selectbox("Category",TASKS); due=st.date_input("Due date",date.today()); notes=st.text_area("Notes")
            if st.form_submit_button("Save task"):
                x("INSERT INTO tasks(name,horse_id,assigned_to,category,due_date,status,notes) VALUES(?,?,?,?,?,?,?)",(name,horses.get(horse) if horse!="None" else None,staff,cat,str(due),"Not Started",notes)); st.success("Saved"); st.rerun()
    st.dataframe(q("""SELECT t.id ID,t.name Task,h.name Horse,t.assigned_to Staff,t.category Category,t.due_date Due,t.status Status,t.notes Notes
                      FROM tasks t LEFT JOIN horses h ON t.horse_id=h.id ORDER BY t.due_date"""),hide_index=True,use_container_width=True)

def maintenance_page():
    header("Maintenance","Water trough cleaning and facility upkeep.")
    props=opts("properties")
    with st.expander("➕ Add trough"):
        with st.form("trough"):
            name=st.text_input("Trough name"); prop=st.selectbox("Property",list(props.keys())) if props else None
            freq=st.selectbox("Frequency",["Daily","Weekly","Fortnightly","Monthly"]); last=st.date_input("Last cleaned",date.today()); staff=st.text_input("Staff"); notes=st.text_area("Notes")
            days={"Daily":1,"Weekly":7,"Fortnightly":14,"Monthly":30}[freq]
            if st.form_submit_button("Save trough"):
                x("INSERT INTO troughs(name,property_id,frequency,last_cleaned,next_due,staff,notes) VALUES(?,?,?,?,?,?,?)",(name,props.get(prop) if prop else None,freq,str(last),str(last+timedelta(days=days)),staff,notes)); st.success("Saved"); st.rerun()
    st.dataframe(q("""SELECT tr.id ID,tr.name Trough,p.name Property,tr.frequency Frequency,tr.last_cleaned "Last Cleaned",tr.next_due "Next Due",tr.staff Staff,tr.notes Notes
                      FROM troughs tr LEFT JOIN properties p ON tr.property_id=p.id ORDER BY tr.next_due"""),hide_index=True,use_container_width=True)

def medical_page():
    header("Medical","Vet records, diagnosis notes and follow-ups.")
    horses=opts("horses")
    with st.expander("➕ Log vet visit"):
        with st.form("medical"):
            horse=st.selectbox("Horse",list(horses.keys())) if horses else None
            vet=st.text_input("Vet"); issue=st.text_input("Issue"); treatment=st.text_area("Treatment plan / notes"); follow=st.date_input("Follow-up",date.today()); status=st.selectbox("Status",["Open","Monitoring","Closed"]); notes=st.text_area("Notes")
            if st.form_submit_button("Save record"):
                x("INSERT INTO medical(horse_id,record_date,vet,issue,treatment,follow_up,status,notes) VALUES(?,?,?,?,?,?,?,?)",(horses.get(horse),str(date.today()),vet,issue,treatment,str(follow),status,notes)); st.success("Saved"); st.rerun()
    st.dataframe(q("""SELECT m.id ID,h.name Horse,m.record_date Date,m.vet Vet,m.issue Issue,m.treatment Treatment,m.follow_up "Follow-up",m.status Status
                      FROM medical m JOIN horses h ON m.horse_id=h.id ORDER BY m.record_date DESC"""),hide_index=True,use_container_width=True)

def training_page():
    header("Training","Trackwork, pre-training, spelling and performance notes.")
    horses=opts("horses")
    with st.expander("➕ Add training / work log"):
        with st.form("training"):
            horse=st.selectbox("Horse",list(horses.keys())) if horses else None
            trainer=st.text_input("Trainer"); typ=st.selectbox("Type",["Canter","Gallop","Trot","Barrier Practice","Swimming","Treadmill","Flatwork"])
            dist=st.number_input("Distance (m)",0,10000,1000); tm=st.text_input("Time",placeholder="1:05"); rating=st.slider("Rating",1,10,7); notes=st.text_area("Notes")
            if st.form_submit_button("Save log"):
                x("INSERT INTO training(horse_id,trainer,type,session_date,distance,time,rating,notes) VALUES(?,?,?,?,?,?,?,?)",(horses.get(horse),trainer,typ,str(date.today()),dist,tm,rating,notes)); st.success("Saved"); st.rerun()
    st.dataframe(q("""SELECT tr.id ID,h.name Horse,tr.trainer Trainer,tr.type Type,tr.session_date Date,tr.distance Distance,tr.time Time,tr.rating Rating,tr.notes Notes
                      FROM training tr JOIN horses h ON tr.horse_id=h.id ORDER BY tr.session_date DESC"""),hide_index=True,use_container_width=True)

def transfers_page():
    header("Transfers","Move horses between properties and programs without losing history.")
    horses=opts("horses"); props=opts("properties")
    with st.expander("➕ Transfer horse"):
        with st.form("transfer"):
            horse=st.selectbox("Horse",list(horses.keys())) if horses else None
            fromp=st.text_input("From property"); top=st.selectbox("To property",list(props.keys())) if props else None
            program=st.selectbox("Program on arrival",PROGRAMS); notes=st.text_area("Handover notes")
            if st.form_submit_button("Save transfer"):
                x("INSERT INTO transfers(horse_id,from_property,to_property,transfer_date,program,notes) VALUES(?,?,?,?,?,?)",(horses.get(horse),fromp,top,str(date.today()),program,notes))
                x("UPDATE horses SET property_id=?, program=? WHERE id=?",(props.get(top),program,horses.get(horse)))
                st.success("Transfer saved"); st.rerun()
    st.dataframe(q("""SELECT tf.id ID,h.name Horse,tf.from_property "From",tf.to_property "To",tf.transfer_date Date,tf.program Program,tf.notes Notes
                      FROM transfers tf JOIN horses h ON tf.horse_id=h.id ORDER BY tf.transfer_date DESC"""),hide_index=True,use_container_width=True)

def billing_page():
    header("Billing","Base day rates, chargeable items, raceday fees and invoice generation.")
    tab1, tab2, tab3, tab4 = st.tabs(["Program Rates", "Chargeable Items", "Horse Charges", "Generate Invoice"])

    with tab1:
        with st.form("rate"):
            program=st.selectbox("Program", PROGRAMS)
            rate=st.number_input("Base day rate", min_value=0.0, value=0.0, step=5.0)
            notes=st.text_area("Notes")
            if st.form_submit_button("Save / update rate"):
                existing=q("SELECT id FROM program_rates WHERE program=?",(program,))
                if existing.empty:
                    x("INSERT INTO program_rates(program,base_day_rate,notes) VALUES(?,?,?)",(program,rate,notes))
                else:
                    x("UPDATE program_rates SET base_day_rate=?, notes=? WHERE program=?",(rate,notes,program))
                st.success("Saved"); st.rerun()
        st.dataframe(q("SELECT program Program, base_day_rate Rate, notes Notes FROM program_rates ORDER BY program"), use_container_width=True, hide_index=True)

    with tab2:
        with st.form("charge_item"):
            name=st.text_input("Item name")
            category=st.text_input("Category", placeholder="Supplement / Medication / Raceday / Extra service")
            unit=st.text_input("Unit type", placeholder="day / dose / item / event")
            price=st.number_input("Default price", min_value=0.0, value=0.0, step=1.0)
            active=st.checkbox("Active", True)
            notes=st.text_area("Notes")
            if st.form_submit_button("Save item"):
                x("INSERT INTO chargeable_items(name,category,unit_type,default_price,active,notes) VALUES(?,?,?,?,?,?)",(name,category,unit,price,1 if active else 0,notes))
                st.success("Saved"); st.rerun()
        st.dataframe(q("SELECT id ID,name Item,category Category,unit_type Unit,default_price Price,active Active,notes Notes FROM chargeable_items ORDER BY name"), use_container_width=True, hide_index=True)

    with tab3:
        horses=opts("horses"); charges=opts("chargeable_items")
        with st.form("horse_charge"):
            horse=st.selectbox("Horse", list(horses.keys())) if horses else None
            charge=st.selectbox("Charge item", list(charges.keys())) if charges else None
            c1,c2=st.columns(2)
            start=c1.date_input("Start date", date.today())
            end=c2.date_input("End date", date.today()+timedelta(days=7))
            qty=st.number_input("Quantity", min_value=0.0, value=1.0, step=0.5)
            freq=st.selectbox("Frequency", ["Daily","Once"])
            notes=st.text_area("Notes")
            if st.form_submit_button("Assign charge"):
                x("INSERT INTO horse_charges(horse_id,charge_item_id,start_date,end_date,quantity,frequency,notes) VALUES(?,?,?,?,?,?,?)",(horses.get(horse),charges.get(charge),str(start),str(end),qty,freq,notes))
                st.success("Charge assigned"); st.rerun()
        st.dataframe(q("""
            SELECT h.name Horse, ci.name Charge, hc.start_date Start, hc.end_date End, hc.quantity Qty, hc.frequency Frequency, ci.default_price Price, hc.notes Notes
            FROM horse_charges hc
            JOIN horses h ON hc.horse_id=h.id
            JOIN chargeable_items ci ON hc.charge_item_id=ci.id
            ORDER BY hc.start_date DESC
        """), use_container_width=True, hide_index=True)

    with tab4:
        owners=opts("owners")
        owner=st.selectbox("Owner", list(owners.keys())) if owners else None
        c1,c2=st.columns(2)
        period_start=c1.date_input("Period start", date.today().replace(day=1))
        period_end=c2.date_input("Period end", date.today())
        if st.button("Preview invoice"):
            owner_id=owners.get(owner)
            preview=build_invoice_preview(owner_id, str(period_start), str(period_end))
            st.dataframe(preview, use_container_width=True, hide_index=True)
            st.metric("Invoice total", f"${preview['Line Total'].sum():,.2f}" if not preview.empty else "$0.00")

        if st.button("Generate invoice"):
            owner_id=owners.get(owner)
            preview=build_invoice_preview(owner_id, str(period_start), str(period_end))
            total=float(preview["Line Total"].sum()) if not preview.empty else 0
            due=str(date.today()+timedelta(days=7))
            x("INSERT INTO invoices(owner_id,invoice_date,period_start,period_end,amount,status,due_date,notes) VALUES(?,?,?,?,?,?,?,?)",(owner_id,str(date.today()),str(period_start),str(period_end),total,"Draft",due,"Generated by StableFlow"))
            invoice_id=int(q("SELECT last_insert_rowid() id").iloc[0].id)
            for _, row in preview.iterrows():
                x("INSERT INTO invoice_items(invoice_id,horse_id,description,quantity,unit_price,line_total) VALUES(?,?,?,?,?,?)",(invoice_id,int(row["Horse ID"]),row["Description"],float(row["Quantity"]),float(row["Unit Price"]),float(row["Line Total"])))
            st.success(f"Invoice generated: ${total:,.2f}")

        st.markdown("### Invoices")
        st.dataframe(q("""
            SELECT i.id ID,o.name Owner,i.invoice_date Date,i.period_start Start,i.period_end End,i.amount Amount,i.status Status,i.due_date Due
            FROM invoices i LEFT JOIN owners o ON i.owner_id=o.id ORDER BY i.invoice_date DESC
        """), use_container_width=True, hide_index=True)

def build_invoice_preview(owner_id, period_start, period_end):
    rows=[]
    horses=q("SELECT id,name,program FROM horses WHERE owner_id=?",(owner_id,))
    for _, h in horses.iterrows():
        rate_df=q("SELECT base_day_rate FROM program_rates WHERE program=?",(h.program,))
        rate=float(rate_df.iloc[0].base_day_rate) if not rate_df.empty else 0
        days=days_overlap(period_start, period_end, period_start, period_end)
        if rate:
            rows.append({"Horse ID":h.id,"Horse":h.name,"Description":f"{h.program} base day rate ({days} days)","Quantity":days,"Unit Price":rate,"Line Total":days*rate})

        charges=q("""
            SELECT hc.start_date,hc.end_date,hc.quantity,hc.frequency,ci.name,ci.default_price
            FROM horse_charges hc JOIN chargeable_items ci ON hc.charge_item_id=ci.id
            WHERE hc.horse_id=?
        """,(int(h.id),))
        for _, ch in charges.iterrows():
            d=days_overlap(period_start, period_end, ch.start_date, ch.end_date)
            if d>0:
                qty = float(ch.quantity) * (d if ch.frequency=="Daily" else 1)
                rows.append({"Horse ID":h.id,"Horse":h.name,"Description":ch["name"],"Quantity":qty,"Unit Price":float(ch.default_price),"Line Total":qty*float(ch.default_price)})

        treatments=q("""
            SELECT product_name,charge_amount,treatment_date,billable
            FROM treatment_log
            WHERE horse_id=? AND billable=1 AND date(treatment_date) BETWEEN date(?) AND date(?)
        """,(int(h.id),period_start,period_end))
        for _, tr in treatments.iterrows():
            rows.append({"Horse ID":h.id,"Horse":h.name,"Description":f"Treatment: {tr.product_name} ({tr.treatment_date})","Quantity":1,"Unit Price":float(tr.charge_amount),"Line Total":float(tr.charge_amount)})

        overrides=q("""
            SELECT fi.name, fi.bill_price_per_unit, fo.quantity, fo.start_date, fo.end_date, fo.billable
            FROM feed_overrides fo JOIN feed_ingredients fi ON fo.ingredient_id=fi.id
            WHERE fo.horse_id=? AND fo.billable=1
        """,(int(h.id),))
        for _, ov in overrides.iterrows():
            d=days_overlap(period_start, period_end, ov.start_date, ov.end_date)
            if d>0:
                qty=float(ov.quantity)*d
                price=float(ov.bill_price_per_unit)
                rows.append({"Horse ID":h.id,"Horse":h.name,"Description":f"Feed override: {ov['name']}","Quantity":qty,"Unit Price":price,"Line Total":qty*price})

        raceday=q("""
            SELECT race_date,racecourse,charge_name,category,amount
            FROM raceday_charges
            WHERE horse_id=? AND billable=1 AND date(race_date) BETWEEN date(?) AND date(?)
        """,(int(h.id),period_start,period_end))
        for _, rc in raceday.iterrows():
            desc=f"Raceday: {rc.charge_name} - {rc.racecourse} ({rc.race_date})"
            rows.append({"Horse ID":h.id,"Horse":h.name,"Description":desc,"Quantity":1,"Unit Price":float(rc.amount),"Line Total":float(rc.amount)})

    return pd.DataFrame(rows, columns=["Horse ID","Horse","Description","Quantity","Unit Price","Line Total"])

init()

with st.sidebar:
    st.markdown("## 🐎 StableFlow")
    st.caption("Stable Operating System")
    st.markdown("<span class='sf-pill'>Raceday + Results Build</span>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("Load sample data"):
        sample(); st.success("Sample data loaded"); st.rerun()
    page=st.radio("Menu",["Dashboard","Owners","Horses","Feed","Treatments","Raceday","Operations","Maintenance","Medical","Training","Transfers","Billing"])

pages={
    "Dashboard":dashboard,
    "Owners":owners_page,
    "Horses":horses_page,
    "Feed":feed_page,
    "Treatments":treatments_page,
    "Raceday":raceday_page,
    "Operations":tasks_page,
    "Maintenance":maintenance_page,
    "Medical":medical_page,
    "Training":training_page,
    "Transfers":transfers_page,
    "Billing":billing_page
}
pages[page]()
