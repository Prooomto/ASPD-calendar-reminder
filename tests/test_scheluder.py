from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.scheluder import schedule_event

def test_schedule_event():
    scheduler = BackgroundScheduler()
    scheduler.start()
    run_time = datetime.now() + timedelta(seconds=1)
    job_id = schedule_event(scheduler, print, run_time, ["ok"])
    assert isinstance(job_id, str)
    scheduler.shutdown()
