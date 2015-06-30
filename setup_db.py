from database import Base, engine, db_session
from models import *
import random



Base.metadata.create_all(bind=engine)

n = 100
#ids = random.sample(range(5000), n)
ids = range(n)

nr_players = 20

for i in ids:
    print(i, i, int(i/nr_players + 1), int(i%nr_players/2))
    db_session.add(Player(i, i, int(i/nr_players + 1), int(i%nr_players/2)))

db_session.commit()
