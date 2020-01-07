import discord
from discord.ext import commands
from discord.voice_client import VoiceClient
import subprocess
from time import sleep
import json
import urllib.request


BOT_TOKEN = 'NDkwMjA2ODAzOTQ3NDIxNzA3.Dn1-RQ.2YrwscHvL2gR865HjSXuexOtEjU'
BOT_ID = '490206803947421707'
BOT_NAME = 'ぅなちゃん'
BOT_ROLE = 'Admin'
OFF_SERVER = ['350289509470175232', '345221462447357952']
DEV_ID = '331741402998374411'

bot = commands.Bot(['<@' + BOT_ID + '>  ', '<@' + BOT_ID + '> ','<@' + BOT_ID + '>'])
bot.remove_command('help')

startup_extensions = ['Music']

@bot.event
async def on_ready():
	print('Start Bot...')
	await bot.change_presence(game=discord.Game(name='ぅな鯖'))

@bot.event
async def on_command_error(error, ctx):
	if isinstance(error, commands.NoPrivateMessage):
		return
	if isinstance(error, commands.MissingRequiredArgument):
		embed = discord.Embed(title=BOT_NAME, color=0xff8080)
		if 'play' in ctx.message.content:
			embed.add_field(name='**＊** __**play**__', value='@' + bot.user.name + '　play　URL・検索ワード', inline=True)
		await bot.send_message(ctx.message.channel, embed=embed)
	elif isinstance(error, commands.DisabledCommand):
		return
	elif isinstance(error, commands.CheckFailure):
		return
	elif isinstance(error, commands.CommandNotFound):
		embed = discord.Embed(title=BOT_NAME, color=0xff8080)
		embed.add_field(name='**＊** __**コマンド**__', value='**・ 使い方**\015@' + bot.user.name + '　コマンド\015( )の中のものでも実行できます', inline=True)
		embed.add_field(name='**＊** __**join**__', value='ボイスルームに\015入ります\015( *j*, *summon* )', inline=True)
		embed.add_field(name='**＊** __**leave**__', value='ボイスルームから\015抜けます\015( *l*, *bye* )', inline=True)
		embed.add_field(name='**＊** __**play**__', value='曲を再生します\015URL・検索ワード\015( *p*, *load* )', inline=True)
		embed.add_field(name='**＊** __**skip**__', value='次の曲を再生します\015( *s*, *next* )', inline=True)
		embed.add_field(name='**＊** __**now**__', value='再生している曲の\015情報を表示します\015( *n*, *playing*, *np* )', inline=True)
		embed.add_field(name='**＊** __**start**__', value='停止している曲を\015再開します\015( *resume* )', inline=True)
		embed.add_field(name='**＊** __**stop**__', value='再生している曲を\015一時停止します\015( *pause* )', inline=True)
		embed.add_field(name='**＊** __**playlist**__', value='予約している曲の\015一覧を表示します\015( *list*, *pl* )', inline=True)
		await bot.send_message(ctx.message.channel, embed=embed)

@bot.command(pass_context=True)
async def server(ctx, arg = 'error'):
	embed = discord.Embed(title=BOT_NAME, color=0xff8080)
	embed.set_footer(text=('権限を持っていません'))
	if ctx.message.server.id in OFF_SERVER:
		if BOT_ROLE in [role.name for role in ctx.message.author.roles]:
			if arg == 'start':
				run = subprocess.call('lsof -i:25565', shell=True)
				if run == 1:
					subprocess.call('./start.sh', shell=True)
					embed.set_footer(text='サーバーの起動を始めます')
				else:
					embed.set_footer(text='サーバーは既に起動しています')
			elif arg == 'restart':
				run = subprocess.call('lsof -i:25565', shell=True)
				if run == 0:
					subprocess.call('./restart.sh', shell=True)
					embed.set_footer(text='サーバーを再起動します')
				else:
					embed.set_footer(text='サーバーは稼働していません')
			else:
				embed.add_field(name='**＊** __**server**__ __**start**__', value='サーバーの起動\015停止時限定', inline=True)
				embed.add_field(name='**＊** __**server**__ __**restart**__', value='サーバーの再起動\015稼働時限定', inline=True)
				embed.add_field(name='**＊** __**reload**__', value='ボットの再起動\015%sが再起動' % bot.user.name, inline=True)
				embed.set_footer(text=('管理'))
	await bot.send_message(ctx.message.channel, embed=embed)

@bot.command(pass_context=True)
async def reload(ctx):
	embed = discord.Embed(title=BOT_NAME, color=0xff8080)
	if ctx.message.author.id == DEV_ID:
		embed.set_footer(text='再起動します')
		await bot.send_message(ctx.message.channel, embed=embed)
		subprocess.call('python3.6 luna.py', shell=True)
		bot.close()
		return
	else:
		embed.set_footer(text=('権限を持っていません'))
		await bot.send_message(ctx.message.channel, embed=embed)

@bot.command(pass_context=True)
async def skin(ctx, id = 'error'):
	embed = discord.Embed(title=BOT_NAME, color=0xff8080)
	await bot.delete_message(ctx.message)
	if id == 'error':
		embed.set_footer(text=('表示するプレイヤーのIDが必要です'))
	else:
		uuid = 'none'
		try:
			api = urllib.request.urlopen('https://api.mojang.com/users/profiles/minecraft/' + id)
		except urllib.error.URLError as e:
			embed.set_footer(text=id + ' 存在しないユーザ名です')
		else:
			data = json.loads(api.read().decode('utf-8'))
#			uuid = data['id']
			id = data['name']
			embed.set_thumbnail(url='http://tt0.link/minecraft/others/skinget/body.php?ID=' + id)
			embed.set_footer(text=(id + " 's skin"))
	await bot.send_message(ctx.message.channel, embed=embed)

if __name__ == '__main__':
	for extension in startup_extensions:
		try:
			bot.load_extension(extension)
		except Exception as e:
			exc = '{}: {}'.format(type(e).__name__, e)
			print('Failed to load extension {}\n{}'.format(extension, exc))

bot.run(BOT_TOKEN)