# src/pipeline_daily.py
import os
import time
import schedule
import subprocess
from db_logger.crud import create_pipeline_run, finish_pipeline_run

# Load environment
CRON_TIME = os.getenv("CRON_TIME", "03:10")  # default 3:10 AM
PYTHON_PATH = os.getenv("PYTHON_PATH", "python3")
SCRAPER_SCRIPT = os.path.join(os.path.dirname(_file_), "happyruh_scraper.py")

def run_pipeline():
    run_id = create_pipeline_run(pipeline_name='daily_sync')
    print(f"🚀 Starting daily HappyRuH sync at {time.strftime('%Y-%m-%d %H:%M:%S')} (run_id={run_id})")

    try:
        result = subprocess.run([PYTHON_PATH, SCRAPER_SCRIPT], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Pipeline failed:", result.stderr or result.stdout)
            finish_pipeline_run(run_id, "error", None, None, result.stderr or result.stdout)
            return

        print("✅ Pipeline completed successfully")
        print(result.stdout[-500:])  # tail log

        finish_pipeline_run(run_id, "ok", None, None, None)
    except Exception as e:
        finish_pipeline_run(run_id, "error", None, None, str(e))
        print("🔥 Error during pipeline:", e)

# -------------------------
# Schedule setup
# -------------------------
hour, minute = map(int, CRON_TIME.split(":"))
schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(run_pipeline)

print(f"🕒 Daily sync scheduled at {CRON_TIME} every day")

# Keep running the scheduler
while True:
    schedule.run_pending()
    time.sleep(30)