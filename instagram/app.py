import os
import json
import time
import dotenv
import random
import logging
from logging.handlers import TimedRotatingFileHandler

import colorama
from termcolor import cprint

import instagrapi
from instagrapi.mixins.challenge import ChallengeChoice
from instagrapi.exceptions import UserNotFound, PleaseWaitFewMinutes

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
handler = TimedRotatingFileHandler("logs/insta.log", when="midnight", interval=1)
handler.suffix = "%Y%m%d"
formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)




class AnnoyApp:
	def __init__(self):
		self.username = os.getenv('iusername')
		self.password = os.getenv('ipassword')

		self.solve_challenge = os.getenv('solve_challenge')


		if "session.json" in os.listdir():
			self.session = json.load(open("session.json", "r"))
			logger.debug("Loaded previous session")
		else:
			self.session = {}


		self.client = instagrapi.Client(settings=self.session)
		
		if self.solve_challenge == "code":
			self.client.challenge_code_handler = self.handleCodeChallenge
		elif self.solve_challenge == "change_password":
			self.client.change_password_handler = self.editPassword

		self.client.login(self.username, self.password)
		with open('session.json', 'w') as f:
			json.dump(self.client.get_settings(), f)

		self.session = json.load(open("session.json", "r"))

		logger.info("Logged in & Saved session details")

		print("<"*10, end=" ")
		cprint("Logged in", "green", end=" ")
		print(">"*10)

	

	def handleCodeChallenge(self, username, choice):
		logger.info("Going through login code challenge")
		
		is_sms_code = choice == ChallengeChoice.sms

		print("A challenge verification is required.")
		code = input(f"Please input the code received by {'sms' if is_sms_code else 'email'}")

		return code

	def editPassword(self, username):
		logger.info("Generating a new password")

		chars = list("abcdefghijklmnopqrstuvwxyz1234567890!&%£$@#_-")
		psw = "".join(random.sample(chars, 32))

		cprint(f"New password = {psw}", "red")
		return psw

	def sleep(self, delay: int):
		logger.debug(f"Sleeping for {delay} seconds")
		try:
			time.sleep(delay)
		except KeyboardInterrupt:
			logging.info("KeyboardInterrupt, exiting.")
			exit()

		logger.debug("Sleep finished")

	@property
	def blacklist(self):
		with open('blacklisted.json', 'r') as f:
			bl = json.load(f)

		logger.debug(f"Fetched {len(bl)} blacklisted users")

		return bl
	
	@property
	def unsubscribed(self):
		with open('unsubscribed.json', 'r') as f:
			unsub = json.load(f)

		logger.debug(f"Fetched {len(unsub)} unsubscribed users")

		return unsub

	@property
	def puns(self):
		# Highly considering doing a web request to my API instead
		with open('puns.json', 'r', encoding='utf-8') as f:
			puns = json.load(f)

		logger.debug(f"Fetched {len(puns.keys())} pun start word")

		return puns

	@property
	def admins(self):
		with open('admins.json', 'r', encoding='utf-8') as f:
			admins = json.load(f)

		logger.debug(f"Fetched {len(admins.keys())} admins")

		return admins


	def getUser(self, by_id: int=0, by_username: str=""):
		if not by_id and not by_username:
			raise ValueError('One of "by_id" or "by_username" parameter must not be empty')

		if by_id:
			try: u = self.client.user_info(by_id)
			except UserNotFound: u = None

		elif by_username:
			try: u = self.client.user_info_by_username(by_username)
			except UserNotFound: u = None

		return u

	def fetchNewMessages(self, delay: int=10):
		fetch = True
		rate_limited = 0
		while fetch:
			logger.info("Checking for new messages")

			try:
				new = self.client.direct_threads(selected_filter="unread")
				new += self.client.direct_pending_inbox()
			except PleaseWaitFewMinutes:
				logger.warning("Too Many Requests..")
				rate_limited += 1
				self.sleep(60*5 *rate_limited)

				continue

			if new:
				logger.info(f"Found {len(new)} new messages")
			else:
				logger.info("No new message found")

			for new_thread_msg in new:
				self.handleNewThreadMessage(new_thread_msg)

			self.sleep(delay)

	def handleNewThreadMessage(self, thread):
		if thread.inviter.pk in self.blacklist:
			logger.debug("Message sender is in blacklist. Ignoring")
			return

		if thread.inviter.pk in self.unsubscribed:
			logger.debug("Message sender unsubscribed from bot. Ignoring")
			return

		# is latest message? # We must check that, at least while we cannot reply to specific msg
		for msg in thread.messages:
			if msg.timestamp < thread.last_activity_at:
				# Consider as seen or too old:
				continue

			else:
				self.handleNewMessage(msg)

	def handleNewMessage(self, message):
		self.client.direct_send_seen(message.thread_id)

		if message.item_type == "action_log":
			logger.info("Not a message but action_log type")
			return

		message.text = message.text.lower()

		if self.isACommand(message):
			return self.handleCommands(message)

		#last_word = message.text.split()[-1] #Punctuation is a problem

		_text = message.text.strip(',;:!?.(){}[]"*') #Punctuation is no more a problem
		if not _text:
			logging.debug("Message empty after punctuation clear.")
			return

		last_word = _text.split()[-1]


		puns = self.puns
		if last_word in puns.keys():
			logger.info("Pun found, sending..")
			self.client.direct_answer(message.thread_id, random.choice(puns[last_word]))
			logger.debug("Sent")
		else:
			logger.info("No pun found..")


	def isACommand(self, message):
		if message.text.startswith('/'):
			return True
		return False

	def handleCommands(self, message):
		prefix, command, args = message.text[0], message.text.split()[0][1:], message.text.split()[1:]
		is_from_admin = message.user_id in self.admins

		if command == "unsubscribe":
			unsubed = self.unsubscribed
			unsubed.append( message.user_id )

			with open('unsubscribed.json', 'w') as f:
				json.dump(unsubed, f)

		elif command == "subscribe":
			unsubed = self.unsubscribed
			unsubed.remove( message.user_id )

			with open('unsubscribed.json', 'w') as f:
				json.dump(unsubed, f)

		elif command in ["addadmin", "add_admin"]:
			if not is_from_admin:
				return

			if not args:
				self.client.direct_answer('❌ New admin username is missing')
				return

			admins = self.admins
			for admin in args:
				a = self.getUser(by_username=admin)
				if a:
					admins.append(a.pk)
				else:
					self.client.direct_answer(f'❌ user "{admin}" not found.')

			with open('admins.json', 'w') as f:
				json.dump(admins, f)

			self.client.direct_answer('✅', message.thread_id)
			return


		else:
			self.client.direct_answer(message.thread_id, "Unknown command..")




app = AnnoyApp()
app.fetchNewMessages()
