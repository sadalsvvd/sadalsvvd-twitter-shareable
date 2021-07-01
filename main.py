from dotenv import load_dotenv
import os
from os import getenv
from time import ctime, sleep, time as pytime
from api import upload_profile_image, get_tweet_count
from store import fetch_ident_json, fetch_ident_redis, commit_ident_def_json, commit_ident_def_redis, IDENTITIES_FILE
import glob
import json
import random
import twitter
load_dotenv(verbose=True)

# Basic algo
# c idents
# d pictures
# interval between character change chosen randomly
# interval between glitch change also chosen randomly (subdivides character change interval)
# json file tracks current pic/char/pics used
# Check tweet frequency every 30m
# - attempt to set up every interval
# - use timer to count when setup should be run
# - tweet frequency affects duration of both intervals
# default change - every 4-12 hrs, reset if i start tweeting??

IDENTITIES_DIR = 'identities'

HEROKU = getenv('HEROKU')
UPLOAD = getenv('UPLOAD')

def generate_ident_data(active_ident, active_glitch, identity_interval, glitch_interval, current_time, tweet_count):
    identities_def = {
        'last_tweet_count_time': current_time,
        'last_tweet_count': tweet_count,
        'active_ident': active_ident,
        'active_glitch': active_glitch,
        'last_identity_time': current_time,
        'last_glitch_time': current_time,
        'identity_interval': identity_interval,
        'glitch_interval': glitch_interval,
        'identities': {}
    }
    identities = [name for name in os.listdir(IDENTITIES_DIR) if os.path.isdir('identities/{}'.format(name))]
    for ident in identities:
        ident_def = {
            'id': ident,
            'files': []
        }

        ident_dir = 'identities/' + ident
        glitch_files = glob.glob('{}/glitch*.jpg'.format(ident_dir))
        for gf in glitch_files:
            used = False
            if gf == active_glitch:
                used = True
            ident_def['files'].append({
                'path': gf,
                'used': used,
            })

        identities_def['identities'][ident] = ident_def
    
    return identities_def

HOURS_16 = 57600
HOURS_48 = 172800

class IdentityManager():
    def __init__(self, upload_profile_pic_func=upload_profile_image, active_ident='1', active_glitch='identities/1/glitch-0.jpg'):
        self.last_check = None
        self.ident_data = None
        self.active_ident = active_ident
        self.active_glitch = active_glitch
        self.upload_profile_pic_func = upload_profile_pic_func
    
    def get_ident_def(self):
        global HEROKU
        if HEROKU:
            return fetch_ident_redis()
        else:
            return fetch_ident_json()
    
    def commit_ident_def(self):
        global HEROKU
        if HEROKU:
            commit_ident_def_redis(self.ident_data)
        else:
            commit_ident_def_json(self.ident_data)
    
    def core_loop(self, mocktime=None, get_tweet_count=get_tweet_count):
        if mocktime is not None:
            current_time = mocktime()
        else:
            current_time = pytime()
        
        # First do base case check
        self.ident_data = self.get_ident_def()
        tweet_count = get_tweet_count()
        print('TWEET COUNT:', tweet_count)
        if self.ident_data is None:
            identity_interval = random.randint(HOURS_16, HOURS_48)
            glitch_interval = random.randint(int(identity_interval / 45), int(identity_interval / 12))
            print('Bootstrapping ident data at {:02f}m / {:02f}m intervals w/ {}: {}...'.format(
                identity_interval / 60,
                glitch_interval / 60,
                self.active_ident,
                self.active_glitch,
                current_time,
            ))
            self.ident_data = generate_ident_data(
                self.active_ident,
                self.active_glitch,
                identity_interval,
                glitch_interval,
                current_time,
                tweet_count,
            )
            self.commit_ident_def()
        
        # If uninitiated or 10m have passed, see if we should update or not
        self.last_check = current_time

        commit_required = False
        tweet_count_change = 0

        # Are we past the last time we checked our tweet count? Let's do so
        if self.last_check > self.ident_data['last_tweet_count_time']:
            tweet_count_change = tweet_count - self.ident_data['last_tweet_count']
            if tweet_count_change > 0:
                self.ident_data['last_tweet_count'] = tweet_count
                self.ident_data['last_tweet_count_time'] = current_time
                commit_required = True
                print(f'Tweet count change: {tweet_count_change}')

        glitch_interval = self.ident_data['glitch_interval']
        identity_interval = self.ident_data['identity_interval']
        # If we've tweeted, adjust the ident_done_at directly and cause a commit to speed up the ident change
        if tweet_count_change > 0:
            # Up to 20 tweets within the check rate will affect the intervals
            glitch_part = glitch_interval / 20
            glitch_subtract = tweet_count_change * glitch_part
            identity_part = identity_interval / 20
            identity_subtract = tweet_count_change * identity_part
            glitch_interval = int(glitch_interval - glitch_subtract)
            identity_interval = int(identity_interval - identity_subtract)

            print('Adjusting glitch_interval from {} to {}'.format(
                self.ident_data['glitch_interval'],
                glitch_interval
            ))
            print('Adjusting identity_interval from {} to {}'.format(
                self.ident_data['identity_interval'],
                identity_interval
            ))
            self.ident_data['glitch_interval'] = glitch_interval
            self.ident_data['identity_interval'] = identity_interval
            commit_required = True

        # Check if we're past the interval for the ident
        glitch_done_at = self.ident_data['last_glitch_time'] + glitch_interval
        ident_done_at = self.ident_data['last_identity_time'] + identity_interval

        ident_done = current_time > ident_done_at
        print('Ident check activated @ {}. Glitch transition at: {}. Ident at: {}'.format(ctime(current_time), ctime(glitch_done_at), ctime(ident_done_at)))

        if ident_done:
            print('IDENT CHANGE: {} is done at {} (> {}).'.format(
                self.ident_data['active_ident'],
                ctime(current_time),
                ctime(self.ident_data['last_identity_time'] + self.ident_data['identity_interval']),
            ))
            random_ident = random.choice(list(self.ident_data['identities'].values()))
            # print(random_ident)
            self.ident_data['active_ident'] = random_ident['id']
            self.ident_data['last_identity_time'] = current_time
            identity_interval = random.randint(HOURS_16, HOURS_48)
            glitch_interval = random.randint(int(identity_interval / 12), int(identity_interval / 6))
            self.ident_data['identity_interval'] = identity_interval
            self.ident_data['glitch_interval'] = glitch_interval
            print('Changing ident to {}.'.format(self.ident_data['active_ident'], random_ident['id']))
            print('Next ident change: {}.'.format(
                ctime(self.ident_data['last_identity_time'] + self.ident_data['identity_interval'])
            ))

            glitch_done = True

            commit_required = True
        else:
            glitch_done = current_time > glitch_done_at
        
        # Get an unused glitch pic
        if glitch_done:
            print('GLITCH CHANGE: {} is done at {} (> {})'.format(
                self.ident_data['active_glitch'],
                ctime(current_time),
                ctime(self.ident_data['last_glitch_time'] + self.ident_data['glitch_interval']),
            ))
            current_ident_glitches = self.ident_data['identities'][str(self.ident_data['active_ident'])]
            all_glitches = list(current_ident_glitches['files'])
            available_glitches = [x for x in all_glitches if x['used'] == False]

            # If we just switched identities or somehow ran out let's reset the state of this set of glitches
            if ident_done or len(available_glitches) == 0:
                for ag in all_glitches:
                    ag['used'] = False

                # lazy af but w/e
                available_glitches = all_glitches
            
            random_available = random.sample(available_glitches, 1)[0]
            self.ident_data['active_glitch'] = random_available['path']
            random_available['used'] = True

            # Reset the last glitch time so we'll properly catch the next one
            self.ident_data['last_glitch_time'] = current_time
            commit_required = True

            if UPLOAD:
                self.upload_profile_pic_func(self.ident_data['active_glitch'])
                print('Uploaded photo {} to Twitter.'.format(self.ident_data['active_glitch']))

        if commit_required == True:
            self.commit_ident_def()

if UPLOAD:
    upload_func = upload_profile_image
else:
    def noop(x):
        pass
    upload_func = noop

# # TEST CODE
# simtime = 1603865418
# def next_simtime():
#     global simtime
#     simtime += 250
#     return simtime

# simtweets = 10
# def next_simtweets():
#     global simtweets
#     simtweets += 3
#     return simtweets

# im = IdentityManager(upload_profile_pic_func=upload_func)
# for _ in range(0, 5):
#     im.core_loop(next_simtime, next_simtweets)

## LOCAL ONLY
if not HEROKU:
    print('Running locally.')
    im = IdentityManager(upload_profile_pic_func=upload_func)
    starttime = pytime()
    while True:
        im.core_loop()
        sleep(60.0 - ((pytime() - starttime) % 60.0))
else:
    print('In Heroku. Scheduler booted up.')
    im = IdentityManager(upload_profile_pic_func=upload_func)
    im.core_loop()



# # debug
# os.unlink(IDENTITIES_FILE)