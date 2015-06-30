import sys
import os
import yaml
import settings
import csv
from io import StringIO

def read_settings():
    try:
        f = open(settings.SETTINGS_FILE, "r")
        return yaml.load(f.read())
    except Exception as e:
        print("Problem reading the settings file!")
        os.system("pause")
        sys.exit()
    

def stats_to_csv():
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

    output = StringIO()
    
    csvwriter = csv.writer(output, delimiter=';')
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

    return output


def session_to_csv(session_nr):
    from database import db_session
    from models import Player

    output = StringIO()
    
    csvwriter = csv.writer(output, delimiter=';')
    csvwriter.writerow(["session nr", "key", "name", "pair", "used"])

    for player in db_session.query(Player).filter_by(session_nr=session_nr).all():
        csvwriter.writerow([player.session_nr, player.key, player.name, player.pair, player.in_use])

    return output
