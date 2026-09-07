-- ====================================================================
-- LOGIX AI ENTERPRISE SECURITY & SEMANTIC LAYER SCRIPT
-- Purpose: Protect the core database from LLM hallucinations and mutations
-- Author: superezzdev
-- ====================================================================

-- 1. Create a dedicated schema for our clean AI views
CREATE SCHEMA LOGIX_VIEWS;
GO

-- 2. Create the Semantic View (Translating legacy schema to clean English)
CREATE VIEW LOGIX_VIEWS.VW_ACTIVE_FLEET AS
SELECT 
    TS_UTC AS [Timestamp],
    V_LAT AS [Latitude],
    V_LON AS [Longitude],
    CAST(IOT_TEMP_VAL_C AS FLOAT) AS [Current_Temperature_C],
    CGO_COND_CD AS [Cargo_Condition_Code],
    RISK_CLS_TXT AS [Risk_Classification],
    DELAY_PROB_DEC AS [Delay_Probability],
    PRT_CNG_LVL AS [Port_Congestion_Level],
    RT_RSK_IDX AS [Route_Risk_Index]
FROM dbo.TBL_SC_FLEET_HIST_RAW;
GO

-- 3. Create a strict Read-Only Login and User for the AI Agent
CREATE LOGIN USR_LOGIX_RO WITH PASSWORD = 'LogixAgentPass2026!';
CREATE USER USR_LOGIX_RO FOR LOGIN USR_LOGIX_RO;
GO

-- 4. Grant access ONLY to the semantic view, explicitly denying everything else
GRANT SELECT ON LOGIX_VIEWS.VW_ACTIVE_FLEET TO USR_LOGIX_RO;
DENY SELECT ON dbo.TBL_SC_FLEET_HIST_RAW TO USR_LOGIX_RO;
DENY INSERT, UPDATE, DELETE, ALTER ON SCHEMA::dbo TO USR_LOGIX_RO;
GO