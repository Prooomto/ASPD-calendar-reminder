from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from src.scheduler import schedule_event

def test_schedule_event_creates_real_job():
    sched = BackgroundScheduler()
    sched.start()
    try:
        run_at = datetime.now() + timedelta(seconds=5)
        job_id = schedule_event(sched, print, run_at, ["ok"])
        assert isinstance(job_id, str)
        job = sched.get_job(job_id)
        assert job is not None
        assert job.trigger.__class__.__name__.lower().startswith("date")
    finally:
        sched.shutdown(wait=False)
