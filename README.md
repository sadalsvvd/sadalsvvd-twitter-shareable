# sadalsvvd-twitter(-shareable)

This repo contains the code I use to update [my avatar on Twitter](https://twitter.com/sadalsvvd) dynamically at regular intervals. It changes the person in the avatar roughly once a day, but also changes the glitch variation in the person in the avatar throughout that time as well. The script also keeps track of how often I have been tweeting; if I tweet a lot during an interval it compresses the time before switching to another person. I did this to remind myself when I am tweeting a lot, but also to make it more likely that someone will notice my picture change if they are reading a tweetstorm of mine.

The avatar pictures live in the `identities` folder, which must contain at plain numbered folders, and must have at least a folder named `1`. Each folder must contain at _least_ a `glitch-0.jpg` file. However, any .jpg file prefixed with `glitch-` will be used by the script after `glitch-0.jpg`, so you could next have `glitch-3.jpg`, `glitch-az.jpg`, etc. but the script will always start by default with the first folder and first identity until state is generated (happens on startup).

If that's confusing, just look in the `identities` folder--you'll get it.

Trivia: in my actual code I use about 40 different characters from thispersondoesnotexist.com and about 10-15 variants run through photomosh.com.

## Adapting for your use

I run this script as a Heroku project with the Heroku Scheduler and Redis To Go add-ons which at these tiers are completely free:

![](https://i.imgur.com/sdCrf8X.png)

Reference for the Heroku scheduler config as I had to fiddle with it a bit:

![](https://i.imgur.com/dl53hqD.png)

Heroku also works well, but if you want to deploy this on your own server it should be fairly trivial to implement a cronjob or in-process timing--whatever works best for your needs.

### Configuration

This script uses the [v1 Twitter API](https://developer.twitter.com/en/docs/twitter-api/v1), so you will need to create a Twitter "standalone application" on the [Twitter Developers site](https://developer.twitter.com/en/portal/projects-and-apps). You will then need to generate twitter access tokens, secrets, and API keys and secrets, and set as them as environment variables:

- TWITTER_ACCESS_TOKEN
- TWITTER_ACCESS_TOKEN_SECRET
- TWITTER_API_KEY
- TWITTER_API_SECRET_KEY

For Heroku deployment, you must set the HEROKU environment variable to `true`. You will also need to set up a [Redis To Go](https://elements.heroku.com/addons/redistogo) instance which is free at the Nano size and has plenty of space for the identity state object (unless you have an absolutely insane number of avatar pictures).

To actually upload, you must set the UPLOAD environment variable to `true` as well. (This exists for local testing. You can also just hardcode out the checks for this variable.)

For reference this is what my Heroku env config looks like (with secret tokens omitted):

![](https://i.imgur.com/GceH58b.png)

### Persistence

A JSON data object containing the state of available images and timing of the last image update gets created and stored in a datastore. My implementation stores this in a free redistogo instance on Heroku. If you want to run this script as a long-running process you can simply store and read from the `identities_def.json` file as a local file.

If it disappears on ephemeral filestore, this is not a big deal as it will regenerate on the next run, _but_ if you blow away this file every time the script runs (such as in a serverless function or Heroku scheduled task without a backing data store) every time the script will reset to your image in `identities/1/glitch-0.jpg` because it will assume you're starting fresh and just want to start with that avatar.

## Support

I offer no support for this code; please don't message or DM me asking for help using it or tweaking it. This is provided for curiosity and reference only.