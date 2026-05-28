# ══════════════════════════════════════════════════════════════════════════════
#  core/database.py — Enterprise Database Layer
#  Strategic Intelligence OS | ARIA Extended Backend
# ══════════════════════════════════════════════════════════════════════════════

import sqlite3
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH     = "db/enterprise_intelligence.db"
CB_DB_PATH  = "db/crunchbase_ecosystem.db"
PROCESSED   = Path("data/processed")

for d in ["data/raw", "data/processed", "db", "config"]:
    Path(d).mkdir(parents=True, exist_ok=True)


# ── Enterprise Operational DB ─────────────────────────────────────────────────

def build_enterprise_db():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS startup_funding (
        id INTEGER PRIMARY KEY, company_name TEXT, sector TEXT,
        funding_round TEXT, amount_usd REAL, valuation_usd REAL,
        investor TEXT, country TEXT, year INTEGER, month INTEGER
    )""")

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
        VALUES (?,?,?,?,?,?,?,?,?)""", funding_data)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sales_pipeline (
        id INTEGER PRIMARY KEY, deal_name TEXT, account TEXT, stage TEXT,
        deal_value REAL, probability REAL, owner TEXT, region TEXT,
        created_date TEXT, close_date TEXT, product TEXT
    )""")
    stages   = ["Prospecting","Qualification","Proposal","Negotiation","Closed Won","Closed Lost"]
    owners   = ["Alice Chen","Bob Patel","Carlos Ruiz","Diana Kim","Ethan Nair"]
    regions  = ["APAC","EMEA","North America","LATAM"]
    products = ["Platform Pro","Analytics Suite","DataBridge","SecureOps","AI Copilot"]
    np.random.seed(42)
    base = datetime(2024,1,1)
    rows = []
    for i in range(60):
        stage = np.random.choice(stages)
        prob  = {"Prospecting":10,"Qualification":25,"Proposal":50,"Negotiation":75,"Closed Won":100,"Closed Lost":0}[stage]
        cr = base + timedelta(days=int(np.random.randint(0,300)))
        cl = cr  + timedelta(days=int(np.random.randint(30,180)))
        rows.append((f"Deal-{i+1:03d}",f"Account-{np.random.randint(1,30):02d}",stage,
                     round(np.random.uniform(10_000,500_000),2),prob,
                     np.random.choice(owners),np.random.choice(regions),
                     cr.strftime("%Y-%m-%d"),cl.strftime("%Y-%m-%d"),np.random.choice(products)))
    cur.executemany("""
        INSERT OR IGNORE INTO sales_pipeline
        (deal_name,account,stage,deal_value,probability,owner,region,created_date,close_date,product)
        VALUES (?,?,?,?,?,?,?,?,?,?)""", rows)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS product_kpis (
        id INTEGER PRIMARY KEY, date TEXT, product TEXT,
        dau INTEGER, mau INTEGER, revenue REAL, churn_rate REAL,
        nps_score REAL, latency_p99_ms REAL, error_rate REAL
    )""")
    kpi_rows = []
    for prod in ["Platform Pro","Analytics Suite","DataBridge"]:
        base_dau = {"Platform Pro":12000,"Analytics Suite":8500,"DataBridge":5200}[prod]
        base_rev = {"Platform Pro":85000,"Analytics Suite":62000,"DataBridge":41000}[prod]
        for w in range(24):
            d = (datetime(2024,1,1)+timedelta(weeks=w)).strftime("%Y-%m-%d")
            t = 1+0.02*w; n = np.random.uniform(0.92,1.08)
            kpi_rows.append((d,prod,int(base_dau*t*n),int(base_dau*t*n*4.2),
                             round(base_rev*t*n,2),round(np.random.uniform(1.2,4.8),2),
                             round(np.random.uniform(38,72),1),round(np.random.uniform(120,450),1),
                             round(np.random.uniform(0.1,1.8),3)))
    cur.executemany("""
        INSERT OR IGNORE INTO product_kpis
        (date,product,dau,mau,revenue,churn_rate,nps_score,latency_p99_ms,error_rate)
        VALUES (?,?,?,?,?,?,?,?,?)""", kpi_rows)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS operational_metrics (
        id INTEGER PRIMARY KEY, timestamp TEXT, service TEXT,
        cpu_pct REAL, memory_pct REAL, request_count INTEGER,
        error_count INTEGER, avg_latency_ms REAL, region TEXT
    )""")
    services = ["API Gateway","ML Inference","Data Pipeline","Auth Service","Query Engine"]
    op_rows  = []
    for i in range(120):
        ts  = (datetime(2024,6,1)+timedelta(hours=i)).strftime("%Y-%m-%d %H:%M:%S")
        svc = np.random.choice(services)
        ano = np.random.random() < 0.08
        op_rows.append((ts,svc,
            round(np.random.uniform(60,95) if ano else np.random.uniform(20,65),1),
            round(np.random.uniform(70,92) if ano else np.random.uniform(30,70),1),
            int(np.random.randint(800,5000)),
            int(np.random.randint(50,300) if ano else np.random.randint(0,20)),
            round(np.random.uniform(400,1200) if ano else np.random.uniform(50,250),1),
            np.random.choice(regions)))
    cur.executemany("""
        INSERT OR IGNORE INTO operational_metrics
        (timestamp,service,cpu_pct,memory_pct,request_count,error_count,avg_latency_ms,region)
        VALUES (?,?,?,?,?,?,?,?)""", op_rows)

    conn.commit(); conn.close()
    return True


def get_db_schema() -> str:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    parts  = []
    for t in tables:
        cur.execute(f"PRAGMA table_info({t})")
        cols   = cur.fetchall()
        col_defs = ", ".join(f"{c[1]} ({c[2]})" for c in cols)
        cur.execute(f"SELECT * FROM {t} LIMIT 2")
        sample = cur.fetchall()
        parts.append(f"TABLE: {t}\n  COLUMNS: {col_defs}\n  SAMPLE: {sample}")
    conn.close()
    return "\n\n".join(parts)


def ensure_databases():
    """Initialize all databases if they don't exist."""
    if not Path(DB_PATH).exists():
        build_enterprise_db()
    if not Path(CB_DB_PATH).exists():
        _build_synthetic_crunchbase()


# ── Synthetic Crunchbase DB ───────────────────────────────────────────────────

def _build_synthetic_crunchbase():
    import json
    np.random.seed(2024)
    sectors   = ["web","mobile","enterprise","biotech","cleantech","fintech","edtech","healthtech","ai","saas","hardware","media","ecommerce"]
    statuses  = ["operating","acquired","closed","ipo"]
    countries = ["USA","GBR","DEU","IND","SGP","BRA","ISR","FRA","CAN","AUS"]
    investor_names = [
        "Sequoia Capital","Andreessen Horowitz","Kleiner Perkins","Benchmark Capital",
        "Accel Partners","GV","Bessemer Venture Partners","Lightspeed","Tiger Global",
        "SoftBank Vision Fund","Coatue Management","CRV","NEA","Khosla Ventures",
        "Founders Fund","Union Square Ventures","Index Ventures","Insight Partners",
        "General Atlantic","Warburg Pincus"
    ] + [f"VentureCapital_{i}" for i in range(21,151)]

    n_companies = 2000; n_people = 500; n_investors = 150
    company_ids   = [f"c:{i}" for i in range(1, n_companies+1)]
    company_names = [f"Company_{i}" for i in range(1, n_companies+1)]
    investor_ids  = [f"f:{i}" for i in range(1, n_investors+1)]
    person_ids    = [f"p:{i}" for i in range(1, n_people+1)]

    conn = sqlite3.connect(CB_DB_PATH)
    cur  = conn.cursor()

    cur.executescript("""
    PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;
    CREATE TABLE IF NOT EXISTS cb_objects (
        id TEXT PRIMARY KEY, entity_type TEXT, entity_id INTEGER, parent_id TEXT,
        name TEXT, normalized_name TEXT, permalink TEXT, category_code TEXT,
        status TEXT, founded_at TEXT, closed_at TEXT, domain TEXT,
        description TEXT, overview TEXT, tag_list TEXT, country_code TEXT,
        state_code TEXT, city TEXT, region TEXT, first_funding_at TEXT,
        last_funding_at TEXT, funding_rounds INTEGER DEFAULT 0,
        funding_total_usd REAL DEFAULT 0, first_milestone_at TEXT,
        last_milestone_at TEXT, milestones INTEGER DEFAULT 0,
        relationships INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT
    );
    CREATE TABLE IF NOT EXISTS cb_acquisitions (
        id INTEGER PRIMARY KEY, acquisition_id INTEGER UNIQUE,
        acquiring_object_id TEXT, acquired_object_id TEXT, term_code TEXT,
        price_amount REAL, price_currency_code TEXT DEFAULT 'USD',
        acquired_at TEXT, source_description TEXT, created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS cb_ipos (
        id INTEGER PRIMARY KEY, ipo_id INTEGER UNIQUE, object_id TEXT,
        valuation_amount REAL, valuation_currency_code TEXT DEFAULT 'USD',
        raised_amount REAL, raised_currency_code TEXT DEFAULT 'USD',
        public_at TEXT, stock_symbol TEXT, created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS cb_people (
        id INTEGER PRIMARY KEY, object_id TEXT UNIQUE, first_name TEXT,
        last_name TEXT, full_name TEXT, birthplace TEXT, affiliation_name TEXT
    );
    CREATE TABLE IF NOT EXISTS cb_funds (
        id INTEGER PRIMARY KEY, fund_id INTEGER UNIQUE, object_id TEXT,
        name TEXT, funded_at TEXT, raised_amount REAL,
        raised_currency_code TEXT DEFAULT 'USD', source_description TEXT, created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS cb_milestones (
        id INTEGER PRIMARY KEY, object_id TEXT, milestone_at TEXT,
        milestone_code TEXT, description TEXT, source_url TEXT,
        source_description TEXT, created_at TEXT
    );
    """)

    descs = [
        "A leading enterprise AI company providing innovative B2B solutions.",
        "Cloud-native platform disrupting the market with cutting-edge technology.",
        "Next-generation analytics platform for Fortune 500 companies.",
        "Enterprise-grade software optimizing operations at scale.",
        "AI-powered automation platform for modern businesses.",
    ]
    obj_rows = []
    for i, (cid, cname) in enumerate(zip(company_ids, company_names)):
        sector = np.random.choice(sectors)
        status = np.random.choice(statuses, p=[0.6,0.2,0.1,0.1])
        fy = np.random.randint(2000, 2022)
        tf = np.random.lognormal(15,2) if np.random.random() > 0.2 else 0
        rounds = int(np.random.randint(0,8)) if tf > 0 else 0
        obj_rows.append((cid,"Company",i+1,None,cname,cname.lower(),cname.lower(),
                         sector,status,f"{fy}-{np.random.randint(1,13):02d}-01",None,
                         f"{cname.lower()}.com",np.random.choice(descs),
                         f"{np.random.choice(descs)} Overview.",
                         f"{sector},{np.random.choice(sectors)}",
                         np.random.choice(countries),None,f"City_{i%50}",None,
                         f"{fy}-{np.random.randint(1,13):02d}-01" if tf>0 else None,
                         f"{fy+rounds}-{np.random.randint(1,13):02d}-01" if tf>0 else None,
                         rounds,round(tf,2),None,None,0,0,"2023-01-01","2024-01-01"))
    for i,(fid,fname) in enumerate(zip(investor_ids,investor_names)):
        obj_rows.append((fid,"FinancialOrg",n_companies+i+1,None,fname,fname.lower(),
                         fname.lower(),"finance","operating",None,None,
                         f"{fname.lower().replace(' ','-')}.com",
                         f"Leading venture capital firm.",
                         "Investment firm overview.","venture capital,finance",
                         np.random.choice(countries[:5]),None,"San Francisco",None,
                         None,None,0,0,None,None,0,0,"2020-01-01","2024-01-01"))

    cur.executemany("""INSERT OR IGNORE INTO cb_objects VALUES
        (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", obj_rows)

    acq_rows = [(i+1,i+1,np.random.choice(investor_ids+company_ids[:50]),
                 np.random.choice(company_ids),np.random.choice(["cash","stock","unknown"]),
                 np.random.lognormal(18,2) if np.random.random()>0.3 else None,"USD",
                 f"{np.random.randint(2000,2023)}-{np.random.randint(1,13):02d}-01",
                 f"Acquisition {i+1}","2023-01-01") for i in range(300)]
    cur.executemany("INSERT OR IGNORE INTO cb_acquisitions VALUES (?,?,?,?,?,?,?,?,?,?)", acq_rows)

    fund_rows = [(i+1,i+1,np.random.choice(investor_ids),
                  f"Fund {np.random.choice(['I','II','III','IV','V'])} - {np.random.randint(2005,2023)}",
                  f"{np.random.randint(2000,2023)}-{np.random.randint(1,13):02d}-01",
                  np.random.lognormal(20,1.5),"USD",
                  f"Venture fund.","2023-01-01") for i in range(200)]
    cur.executemany("INSERT OR IGNORE INTO cb_funds VALUES (?,?,?,?,?,?,?,?,?)", fund_rows)

    ms_descs = ["Launched new product","Reached 1M users","Secured Series A",
                "Opened APAC office","Won industry award","Crossed $10M ARR","Reached profitability"]
    ms_rows = [(i+1,np.random.choice(company_ids),
                f"{np.random.randint(2010,2023)}-{np.random.randint(1,13):02d}-01",
                np.random.choice(["product_launch","funding","partnership","expansion","other"]),
                np.random.choice(ms_descs),None,None,"2023-01-01") for i in range(800)]
    cur.executemany("INSERT OR IGNORE INTO cb_milestones VALUES (?,?,?,?,?,?,?,?)", ms_rows)

    # Indexes
    for idx in [
        "CREATE INDEX IF NOT EXISTS idx_obj_type    ON cb_objects(entity_type)",
        "CREATE INDEX IF NOT EXISTS idx_obj_cat     ON cb_objects(category_code)",
        "CREATE INDEX IF NOT EXISTS idx_obj_status  ON cb_objects(status)",
        "CREATE INDEX IF NOT EXISTS idx_obj_country ON cb_objects(country_code)",
        "CREATE INDEX IF NOT EXISTS idx_obj_funding ON cb_objects(funding_total_usd)",
        "CREATE INDEX IF NOT EXISTS idx_acq_acquirer ON cb_acquisitions(acquiring_object_id)",
        "CREATE INDEX IF NOT EXISTS idx_funds_obj   ON cb_funds(object_id)",
    ]:
        cur.execute(idx)

    conn.commit(); conn.close()


def get_cb_schema() -> str:
    if not Path(CB_DB_PATH).exists():
        return "Crunchbase DB not initialized."
    conn = sqlite3.connect(CB_DB_PATH)
    cur  = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    parts  = []
    for t in tables:
        cur.execute(f"PRAGMA table_info({t})")
        cols = cur.fetchall()
        col_defs = ", ".join(f"{c[1]} ({c[2]})" for c in cols)
        cur.execute(f"SELECT * FROM {t} LIMIT 1")
        sample = cur.fetchall()
        parts.append(f"TABLE: {t}\n  COLUMNS: {col_defs}\n  SAMPLE: {sample}")
    conn.close()
    return "\n\n".join(parts)