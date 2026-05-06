
import sqlite3
from pathlib import Path
from datetime import date, timedelta
import pandas as pd
import streamlit as st

DB_PATH = Path("stableflow.db")
PROGRAMS = ["Agistment", "Spelling", "Pre-Training", "Race Training", "Rehab", "Breaking-In"]
TASKS = ["Feeding", "Maintenance", "Medical", "Training", "Admin", "Transfer"]
MEAL_TIMES = ["AM", "Midday", "PM", "Night"]
UNITS = ["kg", "g", "ml", "scoop", "biscuit", "flake", "tablet", "dose"]

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
    CREATE TABLE IF NOT EXISTS owners(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,phone TEXT,email TEXT,notes TEXT);
    CREATE TABLE IF NOT EXISTS properties(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,location TEXT,notes TEXT);
    CREATE TABLE IF NOT EXISTS horses(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,breed TEXT,owner_id INTEGER,trainer TEXT,property_id INTEGER,program TEXT,status TEXT,notes TEXT);

    CREATE TABLE IF NOT EXISTS feed_ingredients(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        default_unit TEXT,
        cost_per_unit REAL,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS feed_meals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        horse_id INTEGER NOT NULL,
        meal_time TEXT NOT NULL,
        active INTEGER DEFAULT 1,
        prep_notes TEXT,
        FOREIGN KEY(horse_id) REFERENCES horses(id)
    );

    CREATE TABLE IF NOT EXISTS feed_meal_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meal_id INTEGER NOT NULL,
        ingredient_id INTEGER NOT NULL,
        quantity REAL,
        unit TEXT,
        is_supplement INTEGER DEFAULT 0,
        is_medication INTEGER DEFAULT 0,
        notes TEXT,
        FOREIGN KEY(meal_id) REFERENCES feed_meals(id),
        FOREIGN KEY(ingredient_id) REFERENCES feed_ingredients(id)
    );

    CREATE TABLE IF NOT EXISTS feed_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feed_date TEXT,
        horse_id INTEGER,
        meal_time TEXT,
        completed INTEGER DEFAULT 0,
        completed_by TEXT,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,horse_id INTEGER,assigned_to TEXT,category TEXT,due_date TEXT,status TEXT,notes TEXT);
    CREATE TABLE IF NOT EXISTS troughs(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,property_id INTEGER,frequency TEXT,last_cleaned TEXT,next_due TEXT,staff TEXT,notes TEXT);
    CREATE TABLE IF NOT EXISTS medical(id INTEGER PRIMARY KEY AUTOINCREMENT,horse_id INTEGER,record_date TEXT,vet TEXT,issue TEXT,treatment TEXT,follow_up TEXT,status TEXT,notes TEXT);
    CREATE TABLE IF NOT EXISTS training(id INTEGER PRIMARY KEY AUTOINCREMENT,horse_id INTEGER,trainer TEXT,type TEXT,session_date TEXT,distance INTEGER,time TEXT,rating INTEGER,notes TEXT);
    CREATE TABLE IF NOT EXISTS transfers(id INTEGER PRIMARY KEY AUTOINCREMENT,horse_id INTEGER,from_property TEXT,to_property TEXT,transfer_date TEXT,program TEXT,notes TEXT);
    CREATE TABLE IF NOT EXISTS invoices(id INTEGER PRIMARY KEY AUTOINCREMENT,owner_id INTEGER,invoice_date TEXT,amount REAL,status TEXT,due_date TEXT,notes TEXT);
    """)
    c.commit(); c.close()

def q(sql, params=()):
    c = conn()
    df = pd.read_sql_query(sql, c, params=params)
    c.close()
    return df

def x(sql, params=()):
    c = conn()
    c.execute(sql, params)
    c.commit(); c.close()

def opts(table):
    df = q(f"SELECT id,name FROM {table} ORDER BY name")
    return {f"{r['name']} · #{r['id']}": int(r["id"]) for _, r in df.iterrows()}

def sample():
    if not q("SELECT * FROM owners").empty:
        return
    x("INSERT INTO owners(name,phone,email,notes) VALUES(?,?,?,?)",("Topform Syndicate","0400 000 001","syndicate@example.com","Racehorse owners"))
    x("INSERT INTO owners(name,phone,email,notes) VALUES(?,?,?,?)",("Sarah Smith","0400 000 002","sarah@example.com","Spelling client"))
    x("INSERT INTO properties(name,location,notes) VALUES(?,?,?)",("Topform Lodge","North Dandalup","Main property"))
    x("INSERT INTO properties(name,location,notes) VALUES(?,?,?)",("Topform Spelling","Pinjarra","Spelling farm"))
    x("INSERT INTO horses(name,breed,owner_id,trainer,property_id,program,status,notes) VALUES(?,?,?,?,?,?,?,?)",("Topform Star","Thoroughbred",1,"J. Trainer",1,"Race Training","Active","Main sample racehorse"))
    x("INSERT INTO horses(name,breed,owner_id,trainer,property_id,program,status,notes) VALUES(?,?,?,?,?,?,?,?)",("Daisy","Thoroughbred",2,"J. Trainer",2,"Spelling","Active","Sample spelling horse"))
    ingredients = [
        ("Lucerne Chaff","Chaff","kg",1.70,""),
        ("Performance Pellets","Pellets","kg",1.52,""),
        ("Oaten Hay","Hay","biscuit",4.00,""),
        ("Electrolytes","Supplement","g",0.20,""),
        ("Joint Supplement","Supplement","scoop",2.50,""),
        ("Medication","Medication","dose",0.00,"")
    ]
    for item in ingredients:
        x("INSERT INTO feed_ingredients(name,category,default_unit,cost_per_unit,notes) VALUES(?,?,?,?,?)", item)
    # AM meal horse 1
    x("INSERT INTO feed_meals(horse_id,meal_time,active,prep_notes) VALUES(?,?,?,?)",(1,"AM",1,"Feed dry. Check water after."))
    x("INSERT INTO feed_meal_items(meal_id,ingredient_id,quantity,unit,is_supplement,is_medication,notes) VALUES(?,?,?,?,?,?,?)",(1,1,2,"kg",0,0,""))
    x("INSERT INTO feed_meal_items(meal_id,ingredient_id,quantity,unit,is_supplement,is_medication,notes) VALUES(?,?,?,?,?,?,?)",(1,4,30,"g",1,0,""))
    # PM meal horse 1
    x("INSERT INTO feed_meals(horse_id,meal_time,active,prep_notes) VALUES(?,?,?,?)",(1,"PM",1,"Add electrolytes after work."))
    x("INSERT INTO feed_meal_items(meal_id,ingredient_id,quantity,unit,is_supplement,is_medication,notes) VALUES(?,?,?,?,?,?,?)",(2,2,1.5,"kg",0,0,""))
    x("INSERT INTO feed_meal_items(meal_id,ingredient_id,quantity,unit,is_supplement,is_medication,notes) VALUES(?,?,?,?,?,?,?)",(2,3,1,"biscuit",0,0,"Overnight hay"))
    # Daisy
    x("INSERT INTO feed_meals(horse_id,meal_time,active,prep_notes) VALUES(?,?,?,?)",(2,"AM",1,"Spelling ration."))
    x("INSERT INTO feed_meal_items(meal_id,ingredient_id,quantity,unit,is_supplement,is_medication,notes) VALUES(?,?,?,?,?,?,?)",(3,1,1,"kg",0,0,""))
    x("INSERT INTO feed_meal_items(meal_id,ingredient_id,quantity,unit,is_supplement,is_medication,notes) VALUES(?,?,?,?,?,?,?)",(3,5,1,"scoop",1,0,"Joint support"))
    x("INSERT INTO tasks(name,horse_id,assigned_to,category,due_date,status,notes) VALUES(?,?,?,?,?,?,?)",("AM feed round",1,"Staff","Feeding",str(date.today()),"Not Started","Sample"))
    x("INSERT INTO troughs(name,property_id,frequency,last_cleaned,next_due,staff,notes) VALUES(?,?,?,?,?,?,?)",("Trough 1",1,"Weekly",str(date.today()-timedelta(days=8)),str(date.today()-timedelta(days=1)),"Staff","Due"))
    x("INSERT INTO medical(horse_id,record_date,vet,issue,treatment,follow_up,status,notes) VALUES(?,?,?,?,?,?,?,?)",(1,str(date.today()),"Dr Smith","Mild soreness","Rest + ice",str(date.today()+timedelta(days=7)),"Open","Sample"))
    x("INSERT INTO training(horse_id,trainer,type,session_date,distance,time,rating,notes) VALUES(?,?,?,?,?,?,?,?)",(1,"J. Trainer","Gallop",str(date.today()),1200,"1:18",8,"Worked strongly"))

def hero():
    st.markdown('<div class="sf-hero"><div class="sf-title">Stable<span class="sf-gold">Flow</span></div><div class="sf-subtitle">Multi-ingredient feeding, tasks, medical, training, racing and horse lifecycle tracking.</div></div>', unsafe_allow_html=True)

def header(title, sub):
    st.markdown(f"## {title}")
    st.caption(sub)
    st.markdown("---")

def dashboard():
    hero()
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("🐎 Horses", int(q("SELECT COUNT(*) n FROM horses").iloc[0].n))
    c2.metric("🥕 Active Meals", int(q("SELECT COUNT(*) n FROM feed_meals WHERE active=1").iloc[0].n))
    c3.metric("✅ Open Tasks", int(q("SELECT COUNT(*) n FROM tasks WHERE status!='Completed'").iloc[0].n))
    c4.metric("💧 Troughs Due", int(q("SELECT COUNT(*) n FROM troughs WHERE next_due<=?",(str(date.today()),)).iloc[0].n))
    st.markdown("### Horses by program")
    df=q("SELECT program, COUNT(*) count FROM horses GROUP BY program")
    if not df.empty:
        st.bar_chart(df.set_index("program"))
    st.markdown("### Today’s Feed Overview")
    st.dataframe(feed_sheet_df(), use_container_width=True, hide_index=True)

def owners_page():
    header("Owners","Manage clients, syndicates and contacts.")
    with st.expander("➕ Add owner"):
        with st.form("owner"):
            name=st.text_input("Name"); phone=st.text_input("Phone"); email=st.text_input("Email"); notes=st.text_area("Notes")
            if st.form_submit_button("Save owner"):
                x("INSERT INTO owners(name,phone,email,notes) VALUES(?,?,?,?)",(name,phone,email,notes)); st.success("Saved"); st.rerun()
    st.dataframe(q("SELECT id ID,name Name,phone Phone,email Email,notes Notes FROM owners ORDER BY name"),hide_index=True,use_container_width=True)

def horses_page():
    header("Horses","One profile across agistment, spelling, pre-training, racing and rehab.")
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
    return q("""
        SELECT h.name as Horse, h.program as Program, fm.meal_time as Meal,
               GROUP_CONCAT(fi.name || ' - ' || fmi.quantity || ' ' || fmi.unit, CHAR(10)) as Ingredients,
               fm.prep_notes as Prep_Notes
        FROM feed_meals fm
        JOIN horses h ON fm.horse_id=h.id
        LEFT JOIN feed_meal_items fmi ON fm.id=fmi.meal_id
        LEFT JOIN feed_ingredients fi ON fmi.ingredient_id=fi.id
        WHERE fm.active=1
        GROUP BY fm.id
        ORDER BY h.name, CASE fm.meal_time WHEN 'AM' THEN 1 WHEN 'Midday' THEN 2 WHEN 'PM' THEN 3 ELSE 4 END
    """)

def feed_page():
    header("Feed","Build proper multi-ingredient feeds for each horse and meal.")
    tab1, tab2, tab3, tab4 = st.tabs(["Daily Feed Sheet", "Add Meal", "Ingredients", "Meal Items"])

    with tab1:
        st.markdown("### Active Multi-Ingredient Feed Sheet")
        st.dataframe(feed_sheet_df(), use_container_width=True, hide_index=True)
        meals = q("""SELECT fm.id, h.name || ' - ' || fm.meal_time as label
                     FROM feed_meals fm JOIN horses h ON fm.horse_id=h.id WHERE fm.active=1 ORDER BY h.name""")
        if not meals.empty:
            choice = st.selectbox("Log meal completed", [f"{r['label']} · meal #{r['id']}" for _, r in meals.iterrows()])
            meal_id = int(choice.split("#")[1])
            completed_by = st.text_input("Completed by")
            notes = st.text_area("Feed log notes")
            if st.button("Mark Meal Completed"):
                meal = q("SELECT horse_id, meal_time FROM feed_meals WHERE id=?", (meal_id,))
                x("INSERT INTO feed_logs(feed_date,horse_id,meal_time,completed,completed_by,notes) VALUES(?,?,?,?,?,?)",
                  (str(date.today()), int(meal.iloc[0].horse_id), meal.iloc[0].meal_time, 1, completed_by, notes))
                st.success("Meal logged")

    with tab2:
        horse_opts = opts("horses")
        with st.form("meal"):
            horse = st.selectbox("Horse", list(horse_opts.keys())) if horse_opts else None
            meal_time = st.selectbox("Meal time", MEAL_TIMES)
            prep = st.text_area("Prep notes", placeholder="e.g. soak 15 min, feed separately, add medication last")
            active = st.checkbox("Active", True)
            if st.form_submit_button("Create Meal"):
                x("INSERT INTO feed_meals(horse_id,meal_time,active,prep_notes) VALUES(?,?,?,?)",
                  (horse_opts.get(horse), meal_time, 1 if active else 0, prep))
                st.success("Meal created")
                st.rerun()

    with tab3:
        with st.form("ingredient"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Ingredient name", placeholder="Lucerne chaff")
            category = c2.text_input("Category", placeholder="Chaff / Pellets / Supplement / Medication")
            unit = c1.selectbox("Default unit", UNITS)
            cost = c2.number_input("Cost per unit", min_value=0.0, value=0.0, step=0.10)
            notes = st.text_area("Notes")
            if st.form_submit_button("Save Ingredient"):
                x("INSERT INTO feed_ingredients(name,category,default_unit,cost_per_unit,notes) VALUES(?,?,?,?,?)",
                  (name, category, unit, cost, notes))
                st.success("Ingredient saved")
                st.rerun()
        st.dataframe(q("SELECT id ID,name Ingredient,category Category,default_unit Unit,cost_per_unit Cost,notes Notes FROM feed_ingredients ORDER BY name"), hide_index=True, use_container_width=True)

    with tab4:
        meals = q("""SELECT fm.id, h.name || ' - ' || fm.meal_time as label
                     FROM feed_meals fm JOIN horses h ON fm.horse_id=h.id WHERE fm.active=1 ORDER BY h.name, fm.meal_time""")
        ingredients = opts("feed_ingredients")
        with st.form("meal_item"):
            meal = st.selectbox("Meal", [f"{r['label']} · meal #{r['id']}" for _, r in meals.iterrows()]) if not meals.empty else None
            ingredient = st.selectbox("Ingredient", list(ingredients.keys())) if ingredients else None
            qty = st.number_input("Quantity", min_value=0.0, value=1.0, step=0.1)
            unit = st.selectbox("Unit", UNITS)
            is_supp = st.checkbox("Supplement")
            is_med = st.checkbox("Medication")
            notes = st.text_area("Notes")
            if st.form_submit_button("Add Ingredient to Meal"):
                meal_id = int(meal.split("#")[1])
                x("INSERT INTO feed_meal_items(meal_id,ingredient_id,quantity,unit,is_supplement,is_medication,notes) VALUES(?,?,?,?,?,?,?)",
                  (meal_id, ingredients.get(ingredient), qty, unit, 1 if is_supp else 0, 1 if is_med else 0, notes))
                st.success("Ingredient added to meal")
                st.rerun()
        st.dataframe(q("""
            SELECT h.name Horse, fm.meal_time Meal, fi.name Ingredient, fmi.quantity Qty, fmi.unit Unit,
                   CASE WHEN fmi.is_supplement=1 THEN 'Yes' ELSE 'No' END Supplement,
                   CASE WHEN fmi.is_medication=1 THEN 'Yes' ELSE 'No' END Medication,
                   fmi.notes Notes
            FROM feed_meal_items fmi
            JOIN feed_meals fm ON fmi.meal_id=fm.id
            JOIN horses h ON fm.horse_id=h.id
            JOIN feed_ingredients fi ON fmi.ingredient_id=fi.id
            ORDER BY h.name, fm.meal_time, fi.name
        """), hide_index=True, use_container_width=True)

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
    header("Medical","Vet records, treatments and follow-ups.")
    horses=opts("horses")
    with st.expander("➕ Log vet visit"):
        with st.form("medical"):
            horse=st.selectbox("Horse",list(horses.keys())) if horses else None
            vet=st.text_input("Vet"); issue=st.text_input("Issue"); treatment=st.text_area("Treatment"); follow=st.date_input("Follow-up",date.today()); status=st.selectbox("Status",["Open","Monitoring","Closed"]); notes=st.text_area("Notes")
            if st.form_submit_button("Save record"):
                x("INSERT INTO medical(horse_id,record_date,vet,issue,treatment,follow_up,status,notes) VALUES(?,?,?,?,?,?,?,?)",(horses.get(horse),str(date.today()),vet,issue,treatment,str(follow),status,notes)); st.success("Saved"); st.rerun()
    st.dataframe(q("""SELECT m.id ID,h.name Horse,m.record_date Date,m.vet Vet,m.issue Issue,m.treatment Treatment,m.follow_up "Follow-up",m.status Status
                      FROM medical m JOIN horses h ON m.horse_id=h.id ORDER BY m.record_date DESC"""),hide_index=True,use_container_width=True)

def training_page():
    header("Training / Racing","Trackwork, pre-training, spelling and performance notes.")
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
    header("Billing","Invoices and account status.")
    owners=opts("owners")
    with st.expander("➕ Add invoice"):
        with st.form("invoice"):
            owner=st.selectbox("Owner",list(owners.keys())) if owners else None
            amount=st.number_input("Amount",0.0,999999.0,0.0,10.0); status=st.selectbox("Status",["Draft","Sent","Paid","Overdue"]); due=st.date_input("Due date",date.today()+timedelta(days=7)); notes=st.text_area("Notes")
            if st.form_submit_button("Save invoice"):
                x("INSERT INTO invoices(owner_id,invoice_date,amount,status,due_date,notes) VALUES(?,?,?,?,?,?)",(owners.get(owner),str(date.today()),amount,status,str(due),notes)); st.success("Saved"); st.rerun()
    st.dataframe(q("""SELECT i.id ID,o.name Owner,i.invoice_date Date,i.amount Amount,i.status Status,i.due_date "Due Date",i.notes Notes
                      FROM invoices i LEFT JOIN owners o ON i.owner_id=o.id ORDER BY i.invoice_date DESC"""),hide_index=True,use_container_width=True)

init()

with st.sidebar:
    st.markdown("## 🐎 StableFlow")
    st.caption("Stable Operating System")
    st.markdown("<span class='sf-pill'>Multi-Ingredient Feed MVP</span>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("Load sample data"):
        sample(); st.success("Sample data loaded"); st.rerun()
    page=st.radio("Menu",["Dashboard","Owners","Horses","Feed","Operations","Maintenance","Medical","Training","Transfers","Billing"])

pages={"Dashboard":dashboard,"Owners":owners_page,"Horses":horses_page,"Feed":feed_page,"Operations":tasks_page,"Maintenance":maintenance_page,"Medical":medical_page,"Training":training_page,"Transfers":transfers_page,"Billing":billing_page}
pages[page]()
