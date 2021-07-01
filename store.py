import json
import redis
import os
from os import getenv

IDENTITIES_FILE = 'identities_def.json'
def fetch_ident_json():
    if os.path.exists(IDENTITIES_FILE):
        with open(IDENTITIES_FILE, 'r') as f:
            return json.load(f)
    else:
        return None

def commit_ident_def_json(ident_data):
    with open(IDENTITIES_FILE, 'w') as f:
        json.dump(ident_data, f)

if getenv('HEROKU'):
    REDISTOGO_URL = getenv('REDISTOGO_URL')
    r = redis.from_url(REDISTOGO_URL)
else:
    r = None

def fetch_ident_redis():
    global r
    result = r.get('ident')
    if result is not None:
        return json.loads(result)
    else:
        return result

def commit_ident_def_redis(ident_data):
    global r
    r.set('ident', json.dumps(ident_data))