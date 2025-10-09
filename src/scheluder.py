from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

def schedule_event(scheduler, func, time, args):
    """Schedules an event and returns job ID."""
    job = scheduler.add_job(func, 'date', run_date=time, args=args)
    return job.id

if __name__ == "__main__":
    # Example of manual scheduler usage
    def test_job(msg):
        print("Test:", msg)

    s = BackgroundScheduler()
    s.start()
    t = datetime.now()
    schedule_event(s, test_job, t, ["Hello"])
