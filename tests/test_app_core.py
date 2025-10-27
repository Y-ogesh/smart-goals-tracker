# tests/test_app_core.py
import importlib
from datetime import date, timedelta

def test_init_db_creates_tables(tmp_db_path):
    db = importlib.import_module("db")
    # simple smoke: ensure we can list goals (no error) after init
    goals = db.list_goals()
    assert isinstance(goals, list)

def test_create_goal_and_steps_crud(tmp_db_path):
    db = importlib.import_module("db")
    # create goal
    gid = db.create_goal("Launch portfolio site", None)
    assert isinstance(gid, int)

    # add steps
    steps = [
        {"order_index": 1, "title": "Design home page", "detail":"wireframe in Figma",
         "metric":"layout ready", "duration_min":60, "why":"foundation", "due_date": None, "done": 0},
        {"order_index": 2, "title": "Write About Me", "detail":"draft copy",
         "metric":"1 page", "duration_min":30, "why":"introduce self", "due_date": None, "done": 0},
    ]
    db.add_steps(gid, steps)
    got = db.get_steps(gid)
    assert len(got) == 2
    assert got[0]["title"] == "Design home page"

    # update one row (mark done + change metric)
    s0 = got[0]
    db.update_step(
        step_id=s0["id"], goal_id=gid, order_index=1, title="Design home page",
        detail="wireframe in Figma", metric="approved layout",
        duration_min=60, why="foundation", due_date=None, done=1
    )
    got2 = db.get_steps(gid)
    assert got2[0]["done"] == 1
    assert got2[0]["metric"] == "approved layout"

def test_add_steps_replace(tmp_db_path):
    db = importlib.import_module("db")
    gid = db.create_goal("Learn Spanish", None)
    db.add_steps(gid, [{"order_index":1, "title":"Step A", "detail":"","metric":"", "duration_min":None, "why":"", "due_date":None, "done":0}])
    assert len(db.get_steps(gid)) == 1
    # replace with new steps
    db.add_steps(gid, [
        {"order_index":1, "title":"New A", "detail":"","metric":"", "duration_min":None, "why":"", "due_date":None, "done":0},
        {"order_index":2, "title":"New B", "detail":"","metric":"", "duration_min":25, "why":"", "due_date":None, "done":0},
    ], replace=True)
    got = db.get_steps(gid)
    titles = [s["title"] for s in got]
    assert titles == ["New A", "New B"]

def test_checkins_unique_and_streaks(tmp_db_path):
    db = importlib.import_module("db")
    gid = db.create_goal("Gym routine", None)

    today = date.today()
    d0 = today.isoformat()
    d1 = (today - timedelta(days=1)).isoformat()
    d2 = (today - timedelta(days=2)).isoformat()

    # insert duplicate for same day -> should not create duplicates (UNIQUE constraint)
    db.checkin(gid, d0)
    db.checkin(gid, d0)
    checks = db.get_checkins(gid)
    assert len(checks) == 1

    # add a short chain: today, yesterday, day before
    db.checkin(gid, d1)
    db.checkin(gid, d2)
    checks = db.get_checkins(gid)
    assert len(checks) == 3

    # strict requires TODAY present to count
    strict = db.compute_streak_strict(gid)
    assert strict >= 1

    # friendly also works if we delete today
    db.delete_checkin(gid, d0)
    strict2 = db.compute_streak_strict(gid)
    friendly2 = db.compute_streak_friendly(gid)
    assert strict2 == 0
    assert friendly2 >= 1  # can anchor on yesterday

def test_report_pdf_bytes(tmp_db_path):
    # Ensure report builds and returns non-empty bytes
    db = importlib.import_module("db")
    rep = importlib.import_module("report")

    gid = db.create_goal("Read 5 books", None)
    db.add_steps(gid, [
        {"order_index":1, "title":"Pick book #1", "detail":"choose from list", "metric":"1 selected",
         "duration_min":15, "why":"start fast", "due_date":None, "done":0}
    ])
    steps = db.get_steps(gid)
    pdf_bytes = rep.build_pdf("Read 5 books", 3, steps, "Good momentum. Keep daily slots.")
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 1000  # a small PDF should be at least ~1KB

def test_utils_date_helpers():
    ut = importlib.import_module("utils")
    ymd = ut.today_ymd()
    assert isinstance(ymd, str) and len(ymd) == 10 and ymd.count("-") == 2

    days = ut.upcoming_days(5)
    assert len(days) == 5
    assert all(isinstance(d, str) and len(d) == 10 for d in days)
