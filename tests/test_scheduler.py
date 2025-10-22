from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

def test_schedule_job_adds_job(monkeypatch):
    # Use scheduler directly; we don't rely on sleep/real time
    sched = BackgroundScheduler()
    sched.start()
    try:
        run_time = datetime.now() + timedelta(seconds=1)
        job = sched.add_job(lambda: None, "date", run_date=run_time)
        assert job.id and sched.get_job(job.id) is not None
    finally:
        sched.shutdown(wait=False)
