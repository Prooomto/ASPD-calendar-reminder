from src.scheduler import schedule_event

class DummyJob:
    def __init__(self, id_):
        self.id = id_

class DummyScheduler:
    def __init__(self):
        self.calls = []
    def add_job(self, func, trigger, run_date, args):
        # фиксируем, что пришли правильные параметры
        self.calls.append((func, trigger, run_date, args))
        return DummyJob("dummy-id-1")

def test_schedule_event_returns_id_and_calls_add_job():
    sch = DummyScheduler()
    def fake_func(*a): pass
    # любая дата — для юнит-теста не важно
    run_date = "2025-01-01T00:00:00"
    job_id = schedule_event(sch, fake_func, run_date, ["ok"])

    assert job_id == "dummy-id-1"
    assert len(sch.calls) == 1
    func, trigger, rd, args = sch.calls[0]
    assert func is fake_func
    assert trigger == "date"
    assert rd == run_date
    assert args == ["ok"]
