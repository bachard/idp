import csv
from database import db_session
from models import Session, Test, Stat, Item, Player

session_columns = [c.name for c in Session.__table__.columns]
test_columns = [c.name for c in Test.__table__.columns]
stat_columns = [c.name for c in Stat.__table__.columns]

session_columns.remove("id")
test_columns.remove("id")
test_columns.remove("session_id")
stat_columns.remove("id")
stat_columns.remove("test_id")

with open("output.csv", 'w') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=';')
    csvwriter.writerow([c.replace("_", " ") for c in (session_columns + test_columns + stat_columns)])
    
    sessions = db_session.query(Session).all()
    for session in sessions:
        session_out = [getattr(session, c) for c in session_columns]
        tests = session.tests
        for test in tests:
            test_out = [getattr(test, c) for c in test_columns]
            stats = test.stats
            # items = test.items
            for stat in stats:
                stat_out = [getattr(stat, c) for c in stat_columns]
                csvwriter.writerow(session_out + test_out + stat_out)
