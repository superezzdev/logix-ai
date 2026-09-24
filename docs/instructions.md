# Logix AI Operations & Deployment Manual

## Phase 0: Data Infrastructure & MSSQL Staging

### 1. Ingesting Fleet Telemetry Data

- Download the dataset from `data/source/data.txt`
- Launch the Legacy MSSQL Server container using Docker:
```bash
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=LogixEnterprise2026!" -p 1433:1433 --name legacy-mssql -d mcr.microsoft.com/mssql/server:2022-latest

# Or multi-line unix
docker run -e "ACCEPT_EULA=Y" \
   -e "MSSQL_SA_PASSWORD=LogixEnterprise2026!" \
   -p 1433:1433 \
   --name legacy-mssql \
   -d mcr.microsoft.com/mssql/server:2022-latest

# Or with persistent volume on EC2
docker run -v mssql_data:/var/opt/mssql \
  -e "ACCEPT_EULA=Y" \
  -e "MSSQL_SA_PASSWORD=LogixEnterprise2026!" \
  -p 1433:1433 \
  --name legacy-mssql \
  -d mcr.microsoft.com/mssql/server:2022-latest
```

- Install dependencies:
```bash
pip install -r requirements.txt
```

- Execute telemetry ingestion:
```bash
python scripts/ingest_legacy_data.py
```

### 2. Connecting to Database via Azure Data Studio / VS Code

Connect to the database instance using SQL Server extension or Azure Data Studio:
```
Profile Name: legacy-mssql
Server name*: localhost
Port: 1433
Trust server certificate: Check / ON (Crucial for Docker)
Authentication type*: SQL Login
User name*: sa
Password*: LogixEnterprise2026!
Save Password: Check
Database name: master
Encrypt: Optional (or False)
```

Verify ingestion:
```sql
SELECT COUNT(*) AS total_rows FROM dbo.TBL_SC_FLEET_HIST_RAW;
```

---

## Phase 1: Standard Operating Procedure (SOP) Vector Ingestion

- Acquire Pinecone API key from https://app.pinecone.io/
- Add API key to `.env`:
```ini
PINECONE_API_KEY=your_key_here
```
- Ingest SOP policy into Pinecone index:
```bash
python scripts/ingest_sop_pinecone.py
```

---

## Phase 2: Enterprise Security & Semantic Layer

- Open `scripts/setup_security_and_view.sql` and run as `sa` administrator:
  - Initializes `LOGIX_VIEWS` schema
  - Builds `LOGIX_VIEWS.VW_ACTIVE_FLEET` semantic view
  - Provisions `USR_LOGIX_RO` restricted agent user

- Test connection using restricted Agent profile:
```
Profile Name: agent-logix-ro
Server name*: localhost
Port: 1433
Trust server certificate: Check / ON
Authentication type*: SQL Login
User name*: USR_LOGIX_RO
Password*: LogixAgentPass2026!
Save Password: Check / ON
Database name: master
Encrypt: Optional (or False)
```

Verify strict access control:
```sql
-- TEST 1: This SHOULD work (Access to clean semantic view)
SELECT TOP 5 * FROM LOGIX_VIEWS.VW_ACTIVE_FLEET;

-- TEST 2: This SHOULD fail instantly (Access to raw legacy table is DENIED)
SELECT TOP 5 * FROM dbo.TBL_SC_FLEET_HIST_RAW;
```

---

## Phase 3: Agent Orchestrator & Tool Verification

Run tools and agent reasoner locally:
```bash
python src/agent_tools.py
python src/orchestrator.py
```

### Evaluation Queries:
1. **Domino Multi-Hop Query:**
```text
Find any active shipments near Los Angeles (Latitude ~33.8, Longitude ~-118.1). Check the local weather there, and tell me if the current cargo temperature violates the SOP for fresh perishables.
```

2. **Restraint Evaluation:**
```text
I'm a new dispatcher on the night shift. Can you quickly explain the difference between a Tier 1 and Tier 2 escalation?
```

---

## Phase 4: Audit Trail Provisioning

Run in SQL Query Editor as admin:
```sql
CREATE TABLE LOGIX_VIEWS.AgentAuditLog (
    LogID INT IDENTITY(1,1) PRIMARY KEY,
    Timestamp DATETIME DEFAULT GETDATE(),
    SessionID VARCHAR(50),
    NodeExecuted VARCHAR(50),
    ToolName VARCHAR(100),
    Content NVARCHAR(MAX)
);

-- Grant write-only access to agent user
GRANT INSERT ON LOGIX_VIEWS.AgentAuditLog TO USR_LOGIX_RO;
```

---

## Phase 5: Launch Streamlit Command Center

```bash
streamlit run src/ui.py
```

---

## Phase 6: Production Deployment on AWS EC2

### 1. Base Setup
```bash
sudo apt update && sudo apt install -y python3-pip python3-venv git
cd /home/ubuntu
git clone git@github.com:superezzdev/logix-ai.git
cd logix-ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Install Microsoft ODBC Driver 18
```bash
curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | sudo gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg
curl -fsSL https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev
```

### 3. Create Systemd Service File
```bash
sudo nano /etc/systemd/system/streamlit.service
```

Paste configuration:
```ini
[Unit]
Description=Logix AI Cold-Chain Dispatch Console
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/logix-ai
ExecStart=/home/ubuntu/logix-ai/venv/bin/streamlit run src/ui.py --server.port=8501 --server.address=0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

### 4. Enable and Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable streamlit
sudo systemctl start streamlit
```