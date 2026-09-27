from pathlib import Path
import pandas as pd
import urllib
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# __file__ is 'scripts/ingest_legacy_data.py'
script_dir = Path(__file__).resolve().parent # points to scripts/
project_root = script_dir.parents[0] # climbs up 1 levels to project root

load_dotenv(project_root / ".env")

data_path = project_root / "data" / "raw" / "dynamic_supply_chain_logistics_dataset.csv"

db_host = os.getenv("SQL_SERVER_HOST", "localhost")
db_port = os.getenv("SQL_SERVER_PORT", "1433")
db_user = os.getenv("SQL_ADMIN_USER")
db_password = os.getenv("SQL_ADMIN_PASSWORD")

# 1. Load the raw dataset
print(f"Loading CSV from {data_path}...")
df = pd.read_csv(data_path)

# 2. Map clean columns to a messy 2000s legacy enterprise schema
legacy_mapping = {
    'timestamp': 'TS_UTC',
    'vehicle_gps_latitude': 'V_LAT',
    'vehicle_gps_longitude': 'V_LON',
    'iot_temperature': 'IOT_TEMP_VAL_C',
    'cargo_condition_status': 'CGO_COND_CD',
    'risk_classification': 'RISK_CLS_TXT',
    'delay_probability': 'DELAY_PROB_DEC',
    'port_congestion_level': 'PRT_CNG_LVL',
    'route_risk_level': 'RT_RSK_IDX'
}

# Keep only the columns we mapped for this demo and rename them
df_legacy = df[list(legacy_mapping.keys())].rename(columns=legacy_mapping)

# Add a fake ingestion flag to make it look like an automated legacy system
df_legacy['SYS_INGEST_FLAG'] = 'Y'

# 3. Connect to Database (PostgreSQL or MSSQL)
sql_dialect = os.getenv("SQL_DIALECT", "postgresql").strip().lower()
db_name = os.getenv("SQL_DATABASE", "logix_db")

print(f"Connecting to {sql_dialect.upper()} Database ({db_host}:{db_port}/{db_name})...")
quoted_pwd = urllib.parse.quote_plus(db_password) if db_password else ""

if sql_dialect in ("postgres", "postgresql", "psql"):
    engine = create_engine(f"postgresql+psycopg2://{db_user}:{quoted_pwd}@{db_host}:{db_port}/{db_name}")
    target_schema = "public"
else:
    try:
        import pymssql
        host = "127.0.0.1" if db_host in ("localhost", "127.0.0.1") else db_host
        engine = create_engine(f"mssql+pymssql://{db_user}:{quoted_pwd}@{host}:{db_port}/master")
    except Exception:
        connection_string = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={db_host},{db_port};"
            f"DATABASE=master;"
            f"UID={db_user};"
            f"PWD={db_password};"
            f"Encrypt=no;"
            f"TrustServerCertificate=yes;"
        )
        params = urllib.parse.quote_plus(connection_string)
        engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
    target_schema = "dbo"

# 4. Ingest data into the messy table name
table_name = 'TBL_SC_FLEET_HIST_RAW'
print(f"Ingesting into {table_name}. This may take a minute...")
df_legacy.to_sql(table_name, engine, if_exists='replace', index=False, schema=target_schema)

print("✅ Legacy data ingestion complete!")