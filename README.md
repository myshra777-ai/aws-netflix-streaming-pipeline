

```markdown
# 🎬 Netflix Streaming Data Pipeline on AWS

An **end-to-end, production-style data engineering project** that ingests Netflix-style streaming events into an **S3 data lake**, transforms them with **AWS Glue**, stores optimized **Parquet files**, and exposes the data for analytics via **Amazon Athena**.  

![AWS](https://img.shields.io/badge/AWS-Glue%20%7C%20Athena%20%7C%20S3-orange?logo=amazonaws)  
![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen)  
![License](https://img.shields.io/badge/License-MIT-blue)

---

## 🚩 Problem Statement
Design a **production-grade ETL pipeline** for Netflix viewing events:

- 📥 Ingest raw streaming events into an **S3 data lake (bronze layer)**  
- 🔄 Transform and optimize data using **AWS Glue (silver layer)**  
- 📊 Store data in **Parquet format** for fast analytics  
- 🔎 Query the data using **Amazon Athena (gold layer)**  
- ⏰ Add **scheduling & monitoring** to make the pipeline production-ready  

---

## 🏗️ Architecture Overview

**Region:** `ap-south-1 (Mumbai)`  
**Bucket:** `myshr-netflix-datalake-ap-south-1`

```mermaid
flowchart TD
    A[Raw Events (CSV/JSON)] -->|Glue Crawler| B[Raw Athena Table]
    B -->|Glue ETL Job| C[Processed Parquet in S3]
    C -->|Glue Crawler| D[Processed Athena Tables]
    D --> E[Analytics Queries in Athena]
    E --> F[CloudWatch Alarms + SNS Notifications]
```

Layers:
- **Bronze (Raw Layer)** → S3 + Glue crawler + Athena raw table  
- **Silver (Processed Layer)** → Parquet + Glue ETL job + Athena processed tables  
- **Gold (Analytics Layer)** → Athena queries for insights  
- **Ops Layer** → Glue triggers + CloudWatch alarms  

---

## 📐 Data Model

**Raw Events Schema:**
- `user_id` 🔑  
- `title_id` 🎞️  
- `event_type` (e.g., `PLAY_START`)  
- `event_ts` (epoch timestamp)  
- `device_type` (mobile, web, TV)  
- `country` (ISO code)  

**Processed Layer:** Same schema, stored in **Parquet + Snappy compression** for efficiency.

---

## ⚙️ AWS Glue ETL Job (PySpark)

📂 Script: `etl/netflix_raw_to_processed.py`

**Steps:**
1. Read raw events from Glue Data Catalog (`raw_netflix_events_rootevents`)  
2. Apply basic data quality checks (`ColumnCount > 0`)  
3. Write to S3 in **Parquet (Snappy)** under `processed/`  
4. Update Athena tables via Glue crawler  

---

## 📊 Athena Analytics Queries

Stored in `sql/`:

- **Total Events**
  ```sql
  SELECT COUNT(*) AS total_events
  FROM raw_netflix_events_rootevents;
  ```

- **Top Movies**
  ```sql
  SELECT title_id, COUNT(*) AS views
  FROM raw_netflix_events_rootevents
  WHERE event_type = 'PLAY_START'
  GROUP BY title_id
  ORDER BY views DESC
  LIMIT 10;
  ```

- **Country Distribution**
  ```sql
  SELECT country, COUNT(*) AS events
  FROM raw_netflix_events_rootevents
  GROUP BY country
  ORDER BY events DESC;
  ```

✅ Example Results:
- 3,010 total events  
- All `PLAY_START` events → `title_id = 100`  
- All events from `country = 'IN'`  

---

## ⏱️ Scheduling & Monitoring

- **Trigger:** `netflix-daily-etl-trigger` → runs Glue job daily at **02:00 AM UTC (07:30 AM IST)**  
- **CloudWatch Alarm:** `netflix-glue-job-high-resource-usage` → monitors Glue job resource usage (>50% threshold)  
- **SNS Notifications:** Email alerts on job failures or anomalies  

---

## 📂 Repository Structure

```text
aws-netflix-streaming-pipeline/
├─ etl/
│  └─ netflix_raw_to_processed.py      # Glue PySpark ETL job
├─ sql/
│  ├─ total_events.sql                 # Total events
│  ├─ top_movies.sql                   # Top titles by views
│  └─ country_distribution.sql         # Events per country
├─ config/
│  └─ netflix_config.json              # Future pipeline configuration
└─ docs/
   └─ README.md                        # Project documentation
```

---

## 🚀 How to Run

1. **Raw Layer Setup** → Upload raw files → Run Glue crawler  
2. **ETL Job** → Execute `netflix_raw_to_processed.py` → Write Parquet to S3  
3. **Processed Crawler** → Update Athena tables  
4. **Analytics** → Run queries in Athena  
5. **Automation** → Enable Glue trigger for daily runs  

---

## 🔮 Future Enhancements
- Advanced transformations (aggregations, serving schema)  
- Partitioning by `event_date` / `country` for Athena cost optimization  
- Richer Glue Data Quality rules (null checks, enums, ranges)  
- BI dashboards in **QuickSight** or **Grafana**  

---

## 💼 Portfolio Use

> “Built an end-to-end Netflix streaming data pipeline on AWS using S3, Glue, and Athena. Implemented a multi-layer data lake (raw, processed, analytics), automated daily ETL with Glue triggers, stored data in Parquet with Snappy compression, and set up CloudWatch monitoring for Glue job resource usage.”

---

```

---

This version adds:
- 🎨 **Visual polish**: emojis, badges, Mermaid diagram.  
- 📊 **Clear sections**: icons for readability.  
- ✅ **Recruiter-ready highlights**: portfolio call‑out at the end.  

