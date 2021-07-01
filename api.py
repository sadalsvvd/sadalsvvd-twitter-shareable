from dotenv import load_dotenv
from os import getenv
import twitter
load_dotenv(verbose=True)

HARDCODED_USERNAME='sadalsvvd'

TWITTER_API_KEY = getenv('TWITTER_API_KEY')
TWITTER_API_SECRET_KEY = getenv('TWITTER_API_SECRET_KEY')
TWITTER_ACCESS_TOKEN = getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = getenv('TWITTER_ACCESS_TOKEN_SECRET')
TWITTER_BEARER_TOKEN = getenv('TWITTER_BEARER_TOKEN')

api = twitter.Api(consumer_key=TWITTER_API_KEY,
                  consumer_secret=TWITTER_API_SECRET_KEY,
                  access_token_key=TWITTER_ACCESS_TOKEN,
                  access_token_secret=TWITTER_ACCESS_TOKEN_SECRET)

# I'll use this later on the iteration that includes tweet frequency.
def get_tweet_count():
    user = api.GetUser(screen_name=HARDCODED_USERNAME)
    return user.statuses_count

def upload_profile_image(glitch_img_path):
    try:
        updated = api.UpdateImage(glitch_img_path)
        print('Successfully uploaded profile image: {}'.format(glitch_img_path))
    except Exception as e:
        print('Failed to upload profile image.')
        print(e)