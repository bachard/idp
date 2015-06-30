import requests
import sys
import random
import time
from threading import Thread
from database import db_session
from models import Connection

Connection.query.delete()
db_session.commit()
# if len(sys.argv) == 2:
#     id_ = int(sys.argv[1])
# else:
#     id_ = 0

n = 10 # number of clients

# ids = random.sample(range(5000), n)
ids = range(n)

print(ids)
print(len(ids))

def run_client(id):
    time.sleep(random.randint(0, 3))
    print("Client number {} available for connection".format(id))
    r = requests.post("http://127.0.0.1:5000/connect/", data={"id":id})
    d = r.json()
    if d["role"] == 0:
        d["role"] = "Client"
    elif d["role"] == 1:
        d["role"] = "MainClient"
    with open("txtfiles/player_{}.txt".format(id), 'w') as f:
        f.write("{}\n{}\n".format(d["role"], d["connected_with"]))
    print(" ---- Reponse: {}".format(d))

threads = [Thread(target=run_client, args=(id,)) for id in ids]

[thread.start() for thread in threads]

[thread.join() for thread in threads]
    
conns = Connection.query.all()

pairs = [(conn.player_id, conn.connected_with, conn.role) for conn in conns]

pairs = sorted(pairs, key=lambda x: x[0])

for (k, v, r) in pairs:
    if not (pairs[v][1]==k and pairs[v][2]!=r):
        print (k, r, v)

