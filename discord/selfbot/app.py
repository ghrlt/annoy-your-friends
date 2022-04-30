import selfcord as discord
from selfcord.ext import commands, tasks

import os
import json
import dotenv
import random

dotenv.load_dotenv()

bot = commands.Bot(command_prefix="!", description="Sometimes makings puns in your servers!")


@bot.event
async def on_ready():
	print("<"*10, f"Logged in as {bot.user.name}#{bot.user.discriminator}", ">"*10)


def getWhiteListed():
	with open('whitelisted.json', 'r') as f:
		wl = json.load(f)

	return wl

def getPuns():
	with open('puns.json', 'r', encoding='utf-8') as f:
		puns = json.load(f)

	return puns


@bot.event
async def on_message(msg):
	wl = getWhiteListed()

	if msg.content.startswith(bot.command_prefix):
		prefix, command, args = msg.content[0], msg.content.split()[0][1:], msg.content.split()[1:]
		is_from_admin = msg.author.id == bot.user.id

		if is_from_admin:
			if command == "whitelist":
				if not args:
					wl.append( msg.channel.id )
					with open('whitelisted.json', 'w') as f:
						json.dump(wl, f)

				else:
					for arg in args:
						if arg.isdigit():
							wl.append( int(arg) )
						else:
							try: 
								ch = await bot.fetch_channel(arg)
								ch = ch.id

								wl.append( ch )
							except:
								await msg.reply(f'❌ Invalid channel/guild "{arg}"')
								continue

					with open('whitelisted.json', 'w') as f:
						json.dump(wl, f)
			
			if command == "unwhitelist":
				if not args:
					wl.remove( msg.channel.id )
					with open('whitelisted.json', 'w') as f:
						json.dump(wl, f)

				else:
					for arg in args:
						if arg.isdigit():
							wl.remove( int(arg) )
						else:
							try: 
								ch = await bot.fetch_channel(arg)
								ch = ch.id

								wl.remove( ch )
							except:
								await msg.reply(f'❌ Invalid channel/guild "{arg}"')
								continue

					with open('whitelisted.json', 'w') as f:
						json.dump(wl, f)

		return


	if not (msg.channel.id in wl or msg.guild.id in wl):
		return

	if msg.author.id == bot.user.id: 
		return

	_content = msg.content.strip(',;:!?.(){}[]"*') #Punctuation is no more a problem
	if not _content:
		return

	last_word = _content.split()[-1]

	puns = getPuns()
	if last_word in puns.keys():
		await msg.reply(random.choice(puns[last_word]))


bot.run(os.getenv('dtoken'))
