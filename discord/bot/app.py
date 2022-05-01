import discord
from discord.ext import commands, tasks

import os
import json
import dotenv
import random

dotenv.load_dotenv()

intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", description="Sometimes makings puns in your servers!", intents=intents)


@bot.event
async def on_ready():
	print("<"*10, f"Logged in as {bot.user.name}#{bot.user.discriminator}", ">"*10)


def getUnsubed():
	with open('unsubscribed.json', 'r') as f:
		unsubed = json.load(f)

	return unsubed

def getBlacklisted():
	with open('blacklisted.json', 'r') as f:
		bl = json.load(f)

	return bl

def getAdmins():
	with open('admins.json', 'r') as f:
		admins = json.load(f)

	return admins

def getPuns():
	with open('puns.json', 'r', encoding='utf-8') as f:
		puns = json.load(f)

	return puns


@bot.event
async def on_message(msg):
	if msg.author.id == bot.user.id: return
	elif msg.author.id in getBlacklisted(): return

	msg.content = msg.content.lower()

	if msg.content.startswith(bot.command_prefix):
		prefix, command, args = msg.content[0], msg.content.split()[0][1:], msg.content.split()[1:]
		is_from_admin = msg.author.id in getAdmins()

		if command == "unsubscribe":
			unsubed = getUnsubed()
			unsubed.append( msg.author.id )
			with open('unsubscribed.json', 'w') as f:
				json.dump(unsubed, f)

			await msg.add_reaction('✅')
		
		elif command == "subscribe":
			unsubed = getUnsubed()
			unsubed.remove( msg.author.id )
			with open('unsubscribed.json', 'w') as f:
				json.dump(unsubed, f)

			await msg.add_reaction('✅')

		else:
			if command in ['add_admin', 'addadmin']:
				if not is_from_admin:
					return

				if not args:
					return await msg.reply("❌ New admin(s) id(s) missing")

				admins = getAdmins()
				for admin in args:
					if not admin.isdigit():
						try:
							admin = await bot.fetch_user(admin.strip('<@>'))
							admin = admin.id
						except:
							await msg.reply(f'❌ Invalid user "{admin}"')
							continue

					admins.append( int(admin) )


				with open('admins.json', 'w') as f:
					json.dump(admins, f)


		return

	elif msg.author.id in getUnsubed(): return


	_content = msg.content.strip(',;:!?.(){}[]"*') #Punctuation is no more a problem
	if not _content:
		return

	last_word = _content.split()[-1]

	puns = getPuns()
	if last_word in puns.keys():
		await msg.reply(random.choice(puns[last_word]))


bot.run(os.getenv('dtoken'))
