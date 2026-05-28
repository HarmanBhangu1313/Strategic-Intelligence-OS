"""
Auto-extracted from ARIA_Strategic_Intelligence_OS.ipynb
"""

# ── Dashboard ─────────────────────────────────────────────────────────────────
try:
    import gradio as gr
    import plotly.graph_objects as go
    import plotly.express as px
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "gradio", "plotly", "-q"])
    import gradio as gr
    import plotly.graph_objects as go
    import plotly.express as px

# ── Env ───────────────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

# ── Directory setup ───────────────────────────────────────────────────────────
for d in ["data/raw", "data/processed", "db", "config"]:
    Path(d).mkdir(parents=True, exist_ok=True)

print("✅ All dependencies loaded.")


DB_PATH = "enterprise_intelligence.db"

    # ── Table 1: Startup Funding Records ──────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS startup_funding (
        id INTEGER PRIMARY KEY,
        company_name TEXT, sector TEXT, funding_round TEXT,
        amount_usd REAL, valuation_usd REAL, investor TEXT,
        country TEXT, year INTEGER, month INTEGER
    )
    """)
    funding_data = [
        ("NeuralEdge AI","AI/ML","Series B",42_000_000,210_000_000,"Sequoia Capital","USA",2024,3),
        ("QuantaHealth","HealthTech","Series A",18_500_000,74_000_000,"Andreessen Horowitz","USA",2024,5),
        ("GridFlow Energy","CleanTech","Seed",3_200_000,16_000_000,"Y Combinator","India",2024,1),
        ("LogiSense","Supply Chain","Series C",95_000_000,475_000_000,"Tiger Global","Singapore",2023,11),
        ("CodeForge","DevTools","Series A",22_000_000,110_000_000,"Accel","UK",2024,7),
        ("DataMesh Labs","Data Infra","Seed",5_500_000,27_500_000,"GV","Germany",2024,2),
        ("FinBridge","FinTech","Series B",67_000_000,335_000_000,"SoftBank","Brazil",2023,9),
        ("AgroVision","AgriTech","Series A",14_000_000,56_000_000,"Khosla Ventures","India",2024,4),
        ("SecureVault","Cybersecurity","Series C",120_000_000,600_000_000,"Coatue","USA",2024,6),
        ("EduPulse","EdTech","Seed",2_800_000,14_000_000,"500 Startups","Nigeria",2024,8),
        ("CloudNative Inc","Cloud","Series D",200_000_000,1_200_000_000,"Blackrock","USA",2023,12),
        ("MediScan AI","HealthTech","Series B",55_000_000,275_000_000,"NEA","USA",2024,9),
        ("RetailIQ","RetailTech","Series A",19_000_000,76_000_000,"Lightspeed","UK",2024,10),
        ("PayStream","FinTech","Seed",4_100_000,20_500_000,"Hustle Fund","Mexico",2024,1),
        ("RoboFlow","Robotics","Series B",38_000_000,190_000_000,"CRV","USA",2023,8),
    ]
    cur.executemany("""
        INSERT OR IGNORE INTO startup_funding
        (company_name,sector,funding_round,amount_usd,valuation_usd,investor,country,year,month)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, funding_data)

    # ── Table 2: Sales Pipeline ───────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sales_pipeline (
        id INTEGER PRIMARY KEY, deal_name TEXT, account TEXT, stage TEXT,
        deal_value REAL, probability REAL, owner TEXT, region TEXT,
        created_date TEXT, close_date TEXT, product TEXT
    )
    """)
    stages = ["Prospecting","Qualification","Proposal","Negotiation","Closed Won","Closed Lost"]
    owners = ["Alice Chen","Bob Patel","Carlos Ruiz","Diana Kim","Ethan Nair"]
    regions = ["APAC","EMEA","North America","LATAM"]
    products = ["Platform Pro","Analytics Suite","DataBridge","SecureOps","AI Copilot"]
    np.random.seed(42)
    pipeline_rows = []
    base_date = datetime(2024, 1, 1)
    for i in range(60):
        stage = np.random.choice(stages)
        prob = {"Prospecting":10,"Qualification":25,"Proposal":50,
                "Negotiation":75,"Closed Won":100,"Closed Lost":0}[stage]
        created = base_date + timedelta(days=int(np.random.randint(0, 300)))
        close = created + timedelta(days=int(np.random.randint(30, 180)))
        pipeline_rows.append((
            f"Deal-{i+1:03d}", f"Account-{np.random.randint(1,30):02d}", stage,
            round(np.random.uniform(10_000, 500_000), 2), prob,
            np.random.choice(owners), np.random.choice(regions),
            created.strftime("%Y-%m-%d"), close.strftime("%Y-%m-%d"),
            np.random.choice(products)
        ))
    cur.executemany("""
        INSERT OR IGNORE INTO sales_pipeline
        (deal_name,account,stage,deal_value,probability,owner,region,created_date,close_date,product)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, pipeline_rows)

    conn.commit()
    conn.close()
    print(f"✅ Enterprise DB built at '{DB_PATH}'")
    print("   Tables: startup_funding | sales_pipeline | product_kpis | operational_metrics")

build_enterprise_db()


RAW = Path("data/raw")
PROCESSED = Path("data/processed")

def categorize_role(title: str) -> str:
    """Derive role category from job title string."""
    t = str(title).lower()
    if any(x in t for x in ["ceo","founder","cto","coo","cfo","president"]):
        return "C-Suite/Founder"
    if any(x in t for x in ["vp","vice president","director"]):
        return "VP/Director"
    if "board" in t or "advisor" in t:
        return "Board/Advisor"
    if any(x in t for x in ["engineer","developer","architect"]):
        return "Engineering"
    return "Other"


def clean_objects(df: pd.DataFrame = None) -> pd.DataFrame:
    """Clean and normalize the objects (core entity) CSV."""
    if df is None:
        p = RAW / "objects.csv"
        if not p.exists():
            print("  ⚠️  objects.csv not found — generating synthetic Crunchbase data")
            return None
        df = pd.read_csv(p, low_memory=False)

    # Filter to usable entity types
    if "entity_type" in df.columns:
        df = df[df["entity_type"].isin(["Company","Person","FinancialOrg"])].copy()

    # Text normalization
    for col in ["name","category_code","status","country_code"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    if "normalized_name" not in df.columns and "name" in df.columns:
        df["normalized_name"] = df["name"].str.lower()
    if "category_code" in df.columns:
        df["category_code"] = df["category_code"].str.lower().replace("nan","unknown").fillna("unknown")
    if "status" in df.columns:
        df["status"] = df["status"].str.lower().replace("nan","unknown").fillna("unknown")
    if "country_code" in df.columns:
        df["country_code"] = df["country_code"].str.upper().replace("NAN","UNKNOWN").fillna("UNKNOWN")

    # Date parsing
    date_cols = ["founded_at","closed_at","first_funding_at","last_funding_at",
                 "first_milestone_at","last_milestone_at","created_at","updated_at"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")

    # Numerics
    for col in ["funding_total_usd","investment_rounds","invested_companies",
                "funding_rounds","milestones","relationships"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Text truncation
    if "overview" in df.columns:
        df["overview"] = df["overview"].fillna("").astype(str).str[:2000]
    if "description" in df.columns:
        df["description"] = df["description"].fillna("").astype(str).str[:500]
    if "tag_list" in df.columns:
        df["tag_list"] = df["tag_list"].fillna("")

    # Drop image columns
    df = df.drop(columns=["logo_url","logo_width","logo_height",
                           "twitter_username","homepage_url"], errors="ignore")

    df.to_csv(PROCESSED / "objects_clean.csv", index=False)
    print(f"  objects: {len(df):,} rows cleaned")
    return df


def clean_acquisitions() -> pd.DataFrame:
    p = RAW / "acquisitions.csv"
    if not p.exists():
        print("  ⚠️  acquisitions.csv not found — skipping")
        return None
    df = pd.read_csv(p, low_memory=False)
    if "acquired_at" in df.columns:
        df["acquired_at"] = pd.to_datetime(df["acquired_at"], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
    if "price_amount" in df.columns:
        df["price_amount"] = pd.to_numeric(df["price_amount"], errors="coerce")
    if "price_currency_code" in df.columns:
        df["price_currency_code"] = df["price_currency_code"].fillna("USD")
    if "term_code" in df.columns:
        df["term_code"] = df["term_code"].fillna("unknown")
    df.to_csv(PROCESSED / "acquisitions_clean.csv", index=False)
    print(f"  acquisitions: {len(df):,} rows cleaned")
    return df


def clean_ipos() -> pd.DataFrame:
    p = RAW / "ipos.csv"
    if not p.exists():
        print("  ⚠️  ipos.csv not found — skipping")
        return None
    df = pd.read_csv(p, low_memory=False)
    if "public_at" in df.columns:
        df["public_at"] = pd.to_datetime(df["public_at"], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
    for col in ["valuation_amount","raised_amount"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df.to_csv(PROCESSED / "ipos_clean.csv", index=False)
    print(f"  ipos: {len(df):,} rows cleaned")
    return df


def clean_people() -> pd.DataFrame:
    p = RAW / "people.csv"
    if not p.exists():
        print("  ⚠️  people.csv not found — skipping")
        return None
    df = pd.read_csv(p, low_memory=False)
    if "first_name" in df.columns and "last_name" in df.columns:
        df["full_name"] = df["first_name"].fillna("") + " " + df["last_name"].fillna("")
        df["full_name"] = df["full_name"].str.strip()
    df.to_csv(PROCESSED / "people_clean.csv", index=False)
    print(f"  people: {len(df):,} rows cleaned")
    return df


def clean_relationships() -> pd.DataFrame:
    p = RAW / "relationships.csv"
    if not p.exists():
        print("  ⚠️  relationships.csv not found — skipping")
        return None
    df = pd.read_csv(p, low_memory=False)
    for col in ["start_at","end_at"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
    if "title" in df.columns:
        df["title"] = df["title"].fillna("Unknown").str.strip()
        df["role_category"] = df["title"].apply(categorize_role)
    df.to_csv(PROCESSED / "relationships_clean.csv", index=False)
    print(f"  relationships: {len(df):,} rows cleaned")
    return df


def clean_offices() -> pd.DataFrame:
    p = RAW / "offices.csv"
    if not p.exists():
        print("  ⚠️  offices.csv not found — skipping")
        return None
    df = pd.read_csv(p, low_memory=False)
    if "country_code" in df.columns:
        df["country_code"] = df["country_code"].str.strip().str.upper().fillna("UNKNOWN")
    if "city" in df.columns:
        df["city"] = df["city"].str.strip().fillna("")
    for col in ["latitude","longitude"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df.to_csv(PROCESSED / "offices_clean.csv", index=False)
    print(f"  offices: {len(df):,} rows cleaned")
    return df


def clean_milestones() -> pd.DataFrame:
    p = RAW / "milestones.csv"
    if not p.exists():
        print("  ⚠️  milestones.csv not found — skipping")
        return None
    df = pd.read_csv(p, low_memory=False)
    if "milestone_at" in df.columns:
        df["milestone_at"] = pd.to_datetime(df["milestone_at"], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
    if "description" in df.columns:
        df["description"] = df["description"].fillna("").astype(str).str[:500]
    if "milestone_code" in df.columns:
        df["milestone_code"] = df["milestone_code"].fillna("other")
    df.to_csv(PROCESSED / "milestones_clean.csv", index=False)
    print(f"  milestones: {len(df):,} rows cleaned")
    return df


def clean_degrees() -> pd.DataFrame:
    p = RAW / "degrees.csv"
    if not p.exists():
        print("  ⚠️  degrees.csv not found — skipping")
        return None
    df = pd.read_csv(p, low_memory=False)
    for col in ["degree_type","subject","institution"]:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")
    if "graduated_at" in df.columns:
        df["graduated_at"] = pd.to_datetime(df["graduated_at"], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
    df.to_csv(PROCESSED / "degrees_clean.csv", index=False)
    print(f"  degrees: {len(df):,} rows cleaned")
    return df


def clean_funds() -> pd.DataFrame:
    p = RAW / "funds.csv"
    if not p.exists():
        print("  ⚠️  funds.csv not found — skipping")
        return None
    df = pd.read_csv(p, low_memory=False)
    if "funded_at" in df.columns:
        df["funded_at"] = pd.to_datetime(df["funded_at"], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
    if "raised_amount" in df.columns:
        df["raised_amount"] = pd.to_numeric(df["raised_amount"], errors="coerce")
    df.to_csv(PROCESSED / "funds_clean.csv", index=False)
    print(f"  funds: {len(df):,} rows cleaned")
    return df


print("🔧 Running Crunchbase preprocessing pipeline...")
clean_objects()
clean_acquisitions()
clean_ipos()
clean_people()
clean_relationships()
clean_offices()
clean_milestones()
clean_degrees()
clean_funds()
print("✅ Preprocessing complete.")


CB_DB_PATH = "db/crunchbase_ecosystem.db"

def generate_synthetic_crunchbase():
    """
    Generate synthetic Crunchbase-schema-compatible data for all 9 tables.
    Called automatically when real CSVs are missing.
    """
    np.random.seed(2024)
    sectors = ["web","mobile","enterprise","biotech","cleantech","fintech",
               "edtech","healthtech","ai","saas","hardware","media","ecommerce"]
    statuses = ["operating","acquired","closed","ipo"]
    countries = ["USA","GBR","DEU","IND","SGP","BRA","ISR","FRA","CAN","AUS"]
    role_cats = ["C-Suite/Founder","VP/Director","Board/Advisor","Engineering","Other"]

    n_companies = 2000
    n_people    = 500
    n_investors = 150

    # ── cb_objects: companies ─────────────────────────────────────────────────
    company_ids = [f"c:{i}" for i in range(1, n_companies+1)]
    company_names = [f"Company_{i}" for i in range(1, n_companies+1)]
    descriptions = [
        f"A {np.random.choice(sectors)} company providing innovative solutions in {np.random.choice(['B2B','B2C','enterprise','consumer'])} markets.",
        f"Leading provider of {np.random.choice(['cloud','AI','mobile','data'])} technology for modern businesses.",
        f"Disrupting the {np.random.choice(sectors)} industry with cutting-edge platform solutions.",
        f"Enterprise-grade software helping Fortune 500 companies optimize operations.",
        f"Next-generation {np.random.choice(['analytics','automation','collaboration'])} platform.",
    ]
    funded_years = np.random.randint(2000, 2022, n_companies)
    objects_rows = []
    for i, (cid, cname) in enumerate(zip(company_ids, company_names)):
        sector = np.random.choice(sectors)
        status = np.random.choice(statuses, p=[0.6, 0.2, 0.1, 0.1])
        funded_yr = funded_years[i]
        total_funding = np.random.lognormal(15, 2) if np.random.random() > 0.2 else 0
        rounds = int(np.random.randint(0, 8)) if total_funding > 0 else 0
        objects_rows.append((
            cid, "Company", i+1, None, cname, cname.lower(), cname.lower(),
            sector, status,
            f"{funded_yr}-{np.random.randint(1,13):02d}-01", None,
            f"{cname.lower()}.com",
            np.random.choice(descriptions),
            f"{np.random.choice(descriptions)} Overview text.",
            f"{sector},{np.random.choice(sectors)}",
            np.random.choice(countries), None, f"City_{i%50}", None,
            f"{funded_yr}-{np.random.randint(1,13):02d}-01" if total_funding > 0 else None,
            f"{funded_yr+rounds}-{np.random.randint(1,13):02d}-01" if total_funding > 0 else None,
            rounds, round(total_funding, 2), None, None, 0, 0,
            "2023-01-01", "2024-01-01"
        ))

    # ── cb_objects: financial orgs (investors) ────────────────────────────────
    investor_ids = [f"f:{i}" for i in range(1, n_investors+1)]
    investor_names = [
        "Sequoia Capital","Andreessen Horowitz","Kleiner Perkins","Benchmark Capital",
        "Accel Partners","GV","Bessemer Venture Partners","Lightspeed",
        "Tiger Global","SoftBank Vision Fund","Coatue Management","CRV",
        "NEA","Khosla Ventures","Founders Fund","Union Square Ventures",
        "Index Ventures","Insight Partners","General Atlantic","Warburg Pincus"
    ] + [f"VentureCapital_{i}" for i in range(21, n_investors+1)]
    for i, (fid, fname) in enumerate(zip(investor_ids, investor_names)):
        objects_rows.append((
            fid, "FinancialOrg", n_companies+i+1, None, fname, fname.lower(), fname.lower(),
            "finance", "operating", None, None, f"{fname.lower().replace(' ','-')}.com",
            f"Leading venture capital firm investing in {np.random.choice(sectors)} startups.",
            "Investment firm overview.", "venture capital,finance",
            np.random.choice(countries[:5]), None, "San Francisco", None,
            None, None, 0, 0, None, None, 0, 0, "2020-01-01", "2024-01-01"
        ))

    # ── cb_objects: people ────────────────────────────────────────────────────
    person_ids = [f"p:{i}" for i in range(1, n_people+1)]
    first_names = ["James","Maria","David","Sarah","Michael","Lisa","John","Emily",
                   "Robert","Anna","William","Jessica","Richard","Amanda","Joseph",
                   "Stephanie","Thomas","Jennifer","Charles","Linda"]
    last_names = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller",
                  "Davis","Wilson","Anderson","Taylor","Thomas","Jackson","White","Harris"]
    for i, pid in enumerate(person_ids):
        fn = np.random.choice(first_names)
        ln = np.random.choice(last_names)
        objects_rows.append((
            pid, "Person", n_companies+n_investors+i+1, None, f"{fn} {ln}",
            f"{fn} {ln}".lower(), f"{fn.lower()}.{ln.lower()}", "person", "operating",
            None, None, None, f"Executive with {np.random.randint(5,25)} years experience.",
            None, None, np.random.choice(countries), None, "Various", None,
            None, None, 0, 0, None, None, 0, 0, "2020-01-01", "2024-01-01"
        ))

    # ── Persist cb_objects ─────────────────────────────────────────────────────
    obj_cols = [
        "id","entity_type","entity_id","parent_id","name","normalized_name","permalink",
        "category_code","status","founded_at","closed_at","domain","description","overview",
        "tag_list","country_code","state_code","city","region",
        "first_funding_at","last_funding_at","funding_rounds","funding_total_usd",
        "first_milestone_at","last_milestone_at","milestones","relationships",
        "created_at","updated_at"
    ]
    df_obj = pd.DataFrame(objects_rows, columns=obj_cols)
    df_obj.to_csv(PROCESSED / "objects_clean.csv", index=False)

    # ── cb_acquisitions ───────────────────────────────────────────────────────
    n_acq = 300
    acq_rows = []
    for i in range(n_acq):
        acq_rows.append((
            i+1, i+1,
            np.random.choice(investor_ids + company_ids[:50]),
            np.random.choice(company_ids),
            np.random.choice(["cash","stock","unknown"]),
            np.random.lognormal(18, 2) if np.random.random() > 0.3 else None,
            "USD",
            f"{np.random.randint(2000,2023)}-{np.random.randint(1,13):02d}-01",
            f"Acquisition {i+1}",
            "2023-01-01"
        ))
    df_acq = pd.DataFrame(acq_rows, columns=[
        "id","acquisition_id","acquiring_object_id","acquired_object_id",
        "term_code","price_amount","price_currency_code","acquired_at",
        "source_description","created_at"
    ])
    df_acq.to_csv(PROCESSED / "acquisitions_clean.csv", index=False)

    # ── cb_ipos ───────────────────────────────────────────────────────────────
    ipo_companies = np.random.choice(company_ids, size=80, replace=False)
    ipo_rows = [(
        i+1, i+1, cid,
        np.random.lognormal(20, 1.5),
        "USD",
        np.random.lognormal(19, 1.5),
        "USD",
        f"{np.random.randint(1998,2023)}-{np.random.randint(1,13):02d}-01",
        f"TICK{i:03d}",
        "2023-01-01"
    ) for i, cid in enumerate(ipo_companies)]
    df_ipos = pd.DataFrame(ipo_rows, columns=[
        "id","ipo_id","object_id","valuation_amount","valuation_currency_code",
        "raised_amount","raised_currency_code","public_at","stock_symbol","created_at"
    ])
    df_ipos.to_csv(PROCESSED / "ipos_clean.csv", index=False)

    # ── cb_people ─────────────────────────────────────────────────────────────
    people_rows = [(
        i+1, pid,
        np.random.choice(first_names), np.random.choice(last_names),
        f"{np.random.choice(first_names)} {np.random.choice(last_names)}",
        np.random.choice(countries), np.random.choice(investor_names[:20])
    ) for i, pid in enumerate(person_ids)]
    df_people = pd.DataFrame(people_rows, columns=[
        "id","object_id","first_name","last_name","full_name","birthplace","affiliation_name"
    ])
    df_people.to_csv(PROCESSED / "people_clean.csv", index=False)

    # ── cb_relationships ──────────────────────────────────────────────────────
    rel_rows = [(
        i+1, i+1,
        np.random.choice(person_ids),
        np.random.choice(company_ids),
        f"{np.random.randint(2000,2020)}-01-01",
        None if np.random.random() > 0.3 else f"{np.random.randint(2021,2024)}-01-01",
        0 if np.random.random() > 0.3 else 1,
        np.random.choice(["CEO","CTO","VP Engineering","Founder","Director","Board Member",
                          "Software Engineer","Product Manager"]),
        np.random.choice(role_cats),
        "2023-01-01"
    ) for i in range(1500)]
    df_rel = pd.DataFrame(rel_rows, columns=[
        "id","relationship_id","person_object_id","relationship_object_id",
        "start_at","end_at","is_past","title","role_category","created_at"
    ])
    df_rel.to_csv(PROCESSED / "relationships_clean.csv", index=False)

    # ── cb_offices ────────────────────────────────────────────────────────────
    offices_rows = [(
        i+1,
        np.random.choice(company_ids + investor_ids),
        i+1, f"HQ Office {i+1}", None, f"123 Main St Suite {i+1}",
        f"City_{i%30}", f"{np.random.randint(10000,99999)}",
        None, np.random.choice(countries),
        round(np.random.uniform(-90, 90), 4),
        round(np.random.uniform(-180, 180), 4)
    ) for i in range(600)]
    df_off = pd.DataFrame(offices_rows, columns=[
        "id","object_id","office_id","description","region","address1",
        "city","zip_code","state_code","country_code","latitude","longitude"
    ])
    df_off.to_csv(PROCESSED / "offices_clean.csv", index=False)

    # ── cb_milestones ─────────────────────────────────────────────────────────
    milestone_descs = [
        "Launched new product line","Reached 1M users","Secured Series A funding",
        "Opened APAC office","Won industry award","Partnership with enterprise client",
        "Launched mobile app","Achieved SOC2 certification","Acquired competitor",
        "Crossed $10M ARR","Reached profitability","Launched in EU market"
    ]
    ms_rows = [(
        i+1,
        np.random.choice(company_ids),
        f"{np.random.randint(2010,2023)}-{np.random.randint(1,13):02d}-01",
        np.random.choice(["product_launch","funding","partnership","award","expansion","other"]),
        np.random.choice(milestone_descs),
        None, None, "2023-01-01"
    ) for i in range(800)]
    df_ms = pd.DataFrame(ms_rows, columns=[
        "id","object_id","milestone_at","milestone_code","description",
        "source_url","source_description","created_at"
    ])
    df_ms.to_csv(PROCESSED / "milestones_clean.csv", index=False)

    # ── cb_degrees ────────────────────────────────────────────────────────────
    degree_rows = [(
        i+1, np.random.choice(person_ids),
        np.random.choice(["BS","MS","MBA","PhD","BA"]),
        np.random.choice(["Computer Science","Business","Engineering","Mathematics","Physics"]),
        np.random.choice(["MIT","Stanford","Harvard","Carnegie Mellon","UC Berkeley",
                          "Oxford","Cambridge","ETH Zurich","Caltech","Princeton"]),
        f"{np.random.randint(1990,2018)}-06-01", "2023-01-01"
    ) for i in range(400)]
    df_deg = pd.DataFrame(degree_rows, columns=[
        "id","object_id","degree_type","subject","institution","graduated_at","created_at"
    ])
    df_deg.to_csv(PROCESSED / "degrees_clean.csv", index=False)

    # ── cb_funds ──────────────────────────────────────────────────────────────
    fund_rows = [(
        i+1, i+1,
        np.random.choice(investor_ids),
        f"Fund {np.random.choice(['I','II','III','IV','V','VI'])} - {np.random.randint(2005,2023)}",
        f"{np.random.randint(2000,2023)}-{np.random.randint(1,13):02d}-01",
        np.random.lognormal(20, 1.5),
        "USD", f"Venture fund raised by {np.random.choice(investor_names[:20])}", "2023-01-01"
    ) for i in range(200)]
    df_funds = pd.DataFrame(fund_rows, columns=[
        "id","fund_id","object_id","name","funded_at","raised_amount",
        "raised_currency_code","source_description","created_at"
    ])
    df_funds.to_csv(PROCESSED / "funds_clean.csv", index=False)

    print("✅ Synthetic Crunchbase data generated:")
    print(f"   objects: {len(df_obj):,} | acquisitions: {len(df_acq):,} | ipos: {len(df_ipos):,}")
    print(f"   people: {len(df_people):,} | relationships: {len(df_rel):,} | offices: {len(df_off):,}")
    print(f"   milestones: {len(df_ms):,} | degrees: {len(df_deg):,} | funds: {len(df_funds):,}")
    return True


# Only generate synthetic data if real CSVs are missing
missing = not (PROCESSED / "objects_clean.csv").exists()
if missing:
    print("🔧 Real CSVs not found. Generating synthetic Crunchbase data...")
    generate_synthetic_crunchbase()
else:
    print("✅ Cleaned CSVs already present in data/processed/")

    CREATE TABLE IF NOT EXISTS cb_objects (
        id TEXT PRIMARY KEY, entity_type TEXT NOT NULL, entity_id INTEGER,
        parent_id TEXT, name TEXT, normalized_name TEXT, permalink TEXT,
        category_code TEXT, status TEXT, founded_at TEXT, closed_at TEXT,
        domain TEXT, description TEXT, overview TEXT, tag_list TEXT,
        country_code TEXT, state_code TEXT, city TEXT, region TEXT,
        first_funding_at TEXT, last_funding_at TEXT,
        funding_rounds INTEGER DEFAULT 0, funding_total_usd REAL DEFAULT 0,
        first_milestone_at TEXT, last_milestone_at TEXT,
        milestones INTEGER DEFAULT 0, relationships INTEGER DEFAULT 0,
        created_at TEXT, updated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS cb_acquisitions (
        id INTEGER PRIMARY KEY, acquisition_id INTEGER UNIQUE,
        acquiring_object_id TEXT, acquired_object_id TEXT,
        term_code TEXT, price_amount REAL, price_currency_code TEXT DEFAULT 'USD',
        acquired_at TEXT, source_description TEXT, created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS cb_ipos (
        id INTEGER PRIMARY KEY, ipo_id INTEGER UNIQUE,
        object_id TEXT, valuation_amount REAL, valuation_currency_code TEXT DEFAULT 'USD',
        raised_amount REAL, raised_currency_code TEXT DEFAULT 'USD',
        public_at TEXT, stock_symbol TEXT, created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS cb_people (
        id INTEGER PRIMARY KEY, object_id TEXT UNIQUE,
        first_name TEXT, last_name TEXT, full_name TEXT,
        birthplace TEXT, affiliation_name TEXT
    );

    CREATE TABLE IF NOT EXISTS cb_relationships (
        id INTEGER PRIMARY KEY, relationship_id INTEGER UNIQUE,
        person_object_id TEXT, relationship_object_id TEXT,
        start_at TEXT, end_at TEXT, is_past INTEGER DEFAULT 0,
        title TEXT, role_category TEXT, created_at TEXT
    );