import sqlite3

def apply():
    conn = sqlite3.connect('C:/Users/ASUS/Documents/Tech Elecon Pvt. Ltd/Project/SmartRecruit/1_Web_Portal_Django/smartrecruit_project/db.sqlite3')
    c = conn.cursor()
    
    print("Adding columns to jobs_useruiprofile...")
    try: c.execute("ALTER TABLE jobs_useruiprofile ADD COLUMN smtp_alerts_enabled bool NOT NULL DEFAULT 1")
    except Exception as e: print(e)
    try: c.execute("ALTER TABLE jobs_useruiprofile ADD COLUMN high_value_ping_enabled bool NOT NULL DEFAULT 1")
    except Exception as e: print(e)

    print("Adding columns to jobs_sentimentlog...")
    try: c.execute("ALTER TABLE jobs_sentimentlog ADD COLUMN confidence_score real NOT NULL DEFAULT 0.0")
    except Exception as e: print(e)
    try: c.execute("ALTER TABLE jobs_sentimentlog ADD COLUMN sentiment_label varchar(50) NULL")
    except Exception as e: print(e)
    try: c.execute("ALTER TABLE jobs_sentimentlog ADD COLUMN stress_level real NOT NULL DEFAULT 0.0")
    except Exception as e: print(e)

    print("Creating jobs_biasauditlog...")
    try:
        c.execute("""
        CREATE TABLE "jobs_biasauditlog" (
            "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
            "audit_date" datetime NOT NULL,
            "fairness_score" real NOT NULL,
            "disparate_impact_ratio" real NOT NULL,
            "equal_opportunity_diff" real NOT NULL,
            "demographics_json" text NOT NULL,
            "is_certified" bool NOT NULL,
            "audit_report" text NOT NULL,
            "has_risk" bool NOT NULL,
            "risk_details" text NOT NULL,
            "job_id" bigint NOT NULL REFERENCES "jobs_jobposting" ("id") DEFERRABLE INITIALLY DEFERRED
        )
        """)
        c.execute("CREATE INDEX jobs_biasauditlog_job_id_idx ON jobs_biasauditlog (job_id);")
    except Exception as e: print(e)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    apply()
