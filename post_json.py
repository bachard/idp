import requests
import json

url = "http://127.0.0.1:1234/upload_json/"

headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

f = open('stats.json', 'r')
stats = json.loads(f.read())

data = {
    'session_id': 1234,
    'world': 'Volcano_TEST',
    'round': 2,
    'player': 6956,
    'stats': stats
}

r = requests.post(url, data=json.dumps(data), headers=headers)

print(r.status_code)
print(r.text)
