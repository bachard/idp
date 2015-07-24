import requests
import json
from random import randint


url = "http://127.0.0.1:1234/upload_json/"

headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

f = open('stats.json', 'r')
stats = json.loads(f.read())

data = {
    'session_id': 1234,
    'world': 'Volcano_TEST',
    'round': randint(1,10),
    'player': 6960,
    'checkpoints': "test",
    'position_over_time': "test",
    'stats': json.dumps(stats)
}

r = requests.post(url, data=json.dumps(data), headers=headers)

print(r.status_code)
print(r.text)
