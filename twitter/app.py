
import os
import json
import time
import dotenv
import random
import urllib.parse
import logging
from logging.handlers import TimedRotatingFileHandler

import colorama
from termcolor import cprint

import tweepy

dotenv.load_dotenv()
colorama.init()

# Silence other loggers
for log_name, log_obj in logging.Logger.manager.loggerDict.items():
     if log_name != __name__:
          log_obj.disabled = True

logging.basicConfig(
	format='%(asctime)s %(levelname)-8s %(message)s',
	level=logging.DEBUG,
	datefmt='%Y-%m-%d %H:%M:%S'
)
if not "logs" in os.listdir(): os.mkdir("logs")

handler = TimedRotatingFileHandler("logs/twitter.log", when="midnight", interval=1)
handler.suffix = "%Y%m%d"
formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)


class TwitterAnnoyApp:
	def __init__(self):
		self.auth = tweepy.OAuthHandler(os.getenv('tapikey'), os.getenv('tapisecret'))
		self.auth.set_access_token(os.getenv('tuseraccesstoken'), os.getenv('tusersecrettoken'))

		api = tweepy.API(self.auth)
		self.client = api

		logger.info("Logged in")

		print("<"*10, end=" ")
		cprint("Logged in", "green", end=" ")
		print(">"*10)


	@property
	def puns(self):
		logger.debug("Fetching puns")

		with open('puns.json', 'r', encoding="utf-8") as f:
			puns = json.load(f)

		return puns


	def createTweet(self, text, **kwargs):
		t = self.client.update_status(text, **kwargs)
		logger.info(f"Wrote tweet {t.id}")
		return t

	def replyToTweet(self, text: str, tweet_id: int, tweet_author_id: int=None, **kwargs):
		if tweet_author_id is None:
			tweet_to_reply_to = self.client.get_status(tweet_id)
			
			tweet_author_id = tweet_to_reply_to.user.id
			tweet_author_name = tweet_to_reply_to.user.screen_name

		if not text[0] == "@":
			if tweet_author_id and not kwargs.get('tweet_author_name'):
				tweet_author_name = self.client.get_user(user_id=tweet_author_id).screen_name

			if not text[1:len(tweet_author_name)] == tweet_author_name:
				text = f"@{tweet_author_name} {text}"

		t = self.client.update_status(text, in_reply_to_status_id=tweet_id, **kwargs)

		logger.info(f"Replied to tweet {tweet_id} ({t.id})")
		return t


	def searchTweets(self, query: str, lang: str="fr", result_type: str="recent", count: int=50, **kwargs):
		logger.debug(f"Searching tweets ({query}, {count})")

		r = self.client.search_tweets(
			q=query, lang=lang, result_type=result_type, count=count,
			**kwargs
		)

		return r

	def getLatestTweetsFrom(self, username: str, count: int=10, **kwargs):
		r = self.client.user_timeline(screen_name=username, count=count, **kwargs)

		logger.debug(f"Obtaining last {count} tweets from {username}")
		return r


	def getTrends(self, place_id: int=23424819, limit: int=10):
		trends = self.client.get_place_trends(id=place_id)[0]
		return trends['trends'][:limit]


bot = TwitterAnnoyApp()

people_to_annoy = [
	"LeoTechMaker", "TiboInShape", "PatrickAdemo", "Mediavenir",
	"Kardowskii", "benjamincode", "LaPvlga", "Meltamaok",
	"Hardisk", "JimmyDeuxFois__", "Elies13700", "_IDVL",
	"ccastanette", "EmmanuelMacron", "Alosyvs", "AypierreMc", 
	"ConseilDenc", "TwittosHumour", "antoninhrlt"
]

while True:

	with open('annoyed.json', 'r') as f:
		atws = json.load(f)
	with open('puns.json', 'r', encoding="utf-8") as f:
		puns = json.load(f)

	for person in people_to_annoy:
		try: tws = bot.getLatestTweetsFrom(username=person, count=2)
		except tweepy.errors.Unauthorized: continue

		reply_to_person = bot.searchTweets(query=f"to:{person}")

		for tw in tws:
			if tw.id in atws:
				continue

			if tw.text.split()[-1] in puns.keys():
				bot.replyToTweet(random.choice(puns[tw.text.split()[-1]]), tw.id, tw.author.id)
				atws.append(tw.id)

				logger.info(f"Replied to {tw.id} ({tw.author.screen_name})")


			for rtw in reply_to_person:
				if rtw.in_reply_to_status_id == tw.id:
					if rtw.id in atws:
						continue

					if rtw.text.split()[-1] in puns.keys():
						bot.replyToTweet(random.choice(puns[rtw.text.split()[-1]]), rtw.id, rtw.author.id)
						atws.append(rtw.id)

						logger.info(f"Replied to {rtw.id} ({rtw.author.screen_name}), which was a reply to {tw.id} ({tw.author.screen_name})")

	for trend in bot.getTrends(limit=10):
		tweets = bot.searchTweets(trend['query'])
		for tw in tweets:
			if tw.id in atws:
				continue

			if tw.text.split()[-1] in puns.keys():
				bot.replyToTweet(random.choice(puns[tw.text.split()[-1]]), tw.id, tw.author.id)
				atws.append(tw.id)

				logger.info(f"Replied to {tw.id} ({tw.author.screen_name}) - From trend {trend['name']}")

	replies_to_bot = bot.searchTweets(query="to:IfQuoiSayFeur")
	for tw in replies_to_bot:
		if tw.id in atws:
			continue
		
		print(tw.id, tw.text, tw.author.screen_name)
		if tw.text.split()[-1] in puns.keys():
			bot.replyToTweet(random.choice(puns[tw.text.split()[-1]]), tw.id, tw.author.id)
			atws.append(tw.id)

			logger.info(f"Replied to {tw.id} ({tw.author.screen_name})")



	with open('annoyed.json', 'w') as f:
		json.dump(atws, f, indent=2)


	time.sleep(120)


#for t in bot.searchTweets(' OR '.join(bot.puns.keys()), count=2):
#	print(t.text, t.truncated, t.author.screen_name)

#print( bot.createTweet('Quoi?') )
#print( bot.replyToTweet("FEUR", 1520761250698911746) )


#print( bot.client.rate_limit_status() )
