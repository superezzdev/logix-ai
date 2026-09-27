-- ====================================================================
-- LOGIX AI POSTGRESQL SECURITY & SEMANTIC LAYER SCRIPT
-- ====================================================================

-- 1. Create a dedicated schema for our clean AI views
CREATE SCHEMA IF NOT EXISTS logix_views;

-- 2. Create the Semantic View (translating legacy schema to clean English)
CREATE OR REPLACE VIEW logix_views.vw_active_fleet AS
SELECT 
    "TS_UTC" AS timestamp,
    "V_LAT" AS latitude,
    "V_LON" AS longitude,
    CAST("IOT_TEMP_VAL_C" AS DOUBLE PRECISION) AS current_temperature_c,
    "CGO_COND_CD" AS cargo_condition_code,
    "RISK_CLS_TXT" AS risk_classification,
    "DELAY_PROB_DEC" AS delay_probability,
    "PRT_CNG_LVL" AS port_congestion_level,
    "RT_RSK_IDX" AS route_risk_index
FROM public."TBL_SC_FLEET_HIST_RAW";

-- 3. Create the Agent Audit Table
CREATE TABLE IF NOT EXISTS logix_views.agentauditlog (
    logid SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sessionid VARCHAR(50),
    nodeexecuted VARCHAR(50),
    toolname VARCHAR(100),
    content TEXT
);

-- 4. Create a strict Read-Only Role for the AI Agent
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'usr_logix_ro') THEN
        CREATE ROLE usr_logix_ro WITH LOGIN PASSWORD 'LogixAgentPass2026!';
    END IF;
END
$$;

-- 5. Grant access ONLY to the semantic view and audit log, explicitly denying raw tables
GRANT USAGE ON SCHEMA logix_views TO usr_logix_ro;
GRANT SELECT ON logix_views.vw_active_fleet TO usr_logix_ro;
GRANT SELECT, INSERT ON logix_views.agentauditlog TO usr_logix_ro;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA logix_views TO usr_logix_ro;

REVOKE ALL ON TABLE public."TBL_SC_FLEET_HIST_RAW" FROM usr_logix_ro;
