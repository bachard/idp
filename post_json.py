"""
Simple script to simulate statistics sending of Minecraft mod
"""
import requests
import json
from random import randint
from utils import read_settings

settings = read_settings()



url = "http://{}:{}/upload_json/".format(settings["server"]["address"], settings["server"]["port"])

headers = {"Content-type": "application/json", "Accept": "text/plain"}

f = open("stats.json", 'r')
stats = json.loads(f.read())

data = {
    "session_id": 1234,
    "world": "Volcano_TEST",
    "round": randint(1,10),
    "player": randint(1,20),
    "checkpoints": "test",
    "position_over_time": "test",
    "solution": "solution 1",
    "stats": json.dumps(stats)
}

r = requests.post(url, data=json.dumps(data), headers=headers)

print(r.status_code)
print(r.text)
