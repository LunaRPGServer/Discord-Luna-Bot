import asyncio
import discord
from discord.ext import commands
if not discord.opus.is_loaded():
	discord.opus.load_opus('opus')

BOT_NAME = 'ぅなちゃん'
SAFE_URL = ['youtube', 'soundcloud', 'nicovideo']

def __init__(self, bot):
	self.bot = bot

class VoiceEntry:
	def __init__(self, message, player):
		self.requester = message.author
		self.channel = message.channel
		self.player = player

	def __str__(self):
		fmt = '{0.title}'
		duration = self.player.duration
		if duration:
			fmt = fmt + '\015\015{0[0]}分 {0[1]}秒'.format(divmod(duration, 60))
		return fmt.format(self.player, self.requester)

class VoiceState:
	def __init__(self, bot):
		self.current = None
		self.voice = None
		self.bot = bot
		self.play_next_song = asyncio.Event()
		self.songs = asyncio.Queue()
		self.skip_votes = set()
		self.audio_player = self.bot.loop.create_task(self.audio_player_task())

	def is_playing(self):
		if self.voice is None or self.current is None:
			return False

		player = self.current.player
		return not player.is_done()

	@property
	def player(self):
		return self.current.player

	def skip(self):
		self.skip_votes.clear()
		if self.is_playing():
			self.player.stop()

	def toggle_next(self):
		self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

	async def audio_player_task(self):
		while True:
			self.play_next_song.clear()
			self.current = await self.songs.get()
			self.current.player.start()
			await self.play_next_song.wait()
class Music:
	def __init__(self, bot):
		self.bot = bot
		self.voice_states = {}

	def get_voice_state(self, server):
		state = self.voice_states.get(server.id)
		if state is None:
			state = VoiceState(self.bot)
			self.voice_states[server.id] = state

		return state

	def __unload(self):
		for state in self.voice_states.values():
			try:
				state.audio_player.cancel()
				if state.voice:
					self.bot.loop.create_task(state.voice.disconnect())
			except:
				pass

	def get_player(self, ctx):
		"""Retrieve the guild player, or generate one."""
		try:
			player = self.players[ctx.guild.id]
		except KeyError:
			player = MusicPlayer(ctx)
			self.players[ctx.guild.id] = player

		return player

	@commands.command(pass_context=True, no_pm=True, aliases = ['j'])
	async def join(self, ctx):
		summoned_channel = ctx.message.author.voice_channel
		if summoned_channel is None:
			embed = discord.Embed(title=BOT_NAME, color=0xff8080)
			embed.set_footer(text=ctx.message.author.name + ' はボイスルームに入っていません')
			await self.bot.send_message(ctx.message.channel, embed=embed)
			return False

		state = self.get_voice_state(ctx.message.server)
		if state.is_playing():
			embed = discord.Embed(title=BOT_NAME, color=0xff8080)
			embed.set_footer(text=BOT_NAME + ' は他のチャンネルで再生中です')
			await self.bot.send_message(ctx.message.channel, embed=embed)
			return False
		if state.voice is None:
			state.voice = await self.bot.join_voice_channel(summoned_channel)
		else:
			await state.voice.move_to(summoned_channel)

		return True

	@commands.command(pass_context=True, no_pm=True, aliases = ['p', 'load'])
	async def play(self, ctx, *, song : str):
		state = self.get_voice_state(ctx.message.server)
		requester = ctx.message.author.name
		opts = {
			'default_search': 'auto',
			'quiet': True,
		}
		bef_option = '-reconnect 1'
		# bef_option = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
		if state.voice is None:
			success = await ctx.invoke(self.join)
			if not success:
				return
		try:
			await self.bot.delete_message(ctx.message)
			if song.startswith('https://youtu.be/'):
				song = song.replace('https://youtu.be/', 'https://www.youtube.com/watch?v=')
			if song.startswith('http'):
				con = False
			else:
				con = True
			for word in SAFE_URL:
				if word in song:
					con = True
			if con == False:
				embed = discord.Embed(title=BOT_NAME, color=0xff8080)
				embed.set_footer(text='対応していないURLです')
				await self.bot.send_message(ctx.message.channel, embed=embed)
				return
			player = await state.voice.create_ytdl_player(song, ytdl_options=opts, before_options=bef_option, after=state.toggle_next)
		except Exception as e:
			fmt = '再生準備中にエラーが発生しました ```py\n{}: {}\n```'
			await self.bot.send_message(ctx.message.channel, fmt.format(type(e).__name__, e))
		else:
			player.volume = 0.15
			entry = VoiceEntry(ctx.message, player)
			embed = discord.Embed(title=BOT_NAME, color=0xff8080)
			embed.set_footer(text='再生します')
			embed.add_field(name='**＊** __**曲名 / 時間**__', value=str(entry), inline=False)
			embed.add_field(name='**＊** __**リクエスト**__', value=requester, inline=False)
			await self.bot.send_message(ctx.message.channel, embed=embed)
			await state.songs.put(entry)

	@commands.command(pass_context=True, no_pm=True, aliases = ['l', 'bye'])
	async def leave(self, ctx):
		server = ctx.message.server
		state = self.get_voice_state(server)

		if state.is_playing():
			player = state.player
			player.stop()

		try:
			state.audio_player.cancel()
			del self.voice_states[server.id]
			await state.voice.disconnect()
		except:
			pass

	@commands.command(pass_context=True, no_pm=True, aliases = ['s', 'next'])
	async def skip(self, ctx):
		state = self.get_voice_state(ctx.message.server)
		if not state.is_playing():
			embed = discord.Embed(title=BOT_NAME, color=0xff8080)
			embed.set_footer(text='現在何も再生していません')
			await self.bot.send_message(ctx.message.channel, embed=embed)
			return

		embed = discord.Embed(title=BOT_NAME, color=0xff8080)
		voter = ctx.message.author
		if voter == state.current.requester:
			embed.set_footer(text=ctx.message.author.name + ' が投票したのでスキップします')
			state.skip()
		elif voter.id not in state.skip_votes:
			state.skip_votes.add(voter.id)
			total_votes = len(state.skip_votes)
			if total_votes >= 3:
				embed.set_footer(text='投票数が達したのでスキップします')
				state.skip()
			else:
				embed.add_field(name='**＊** __**スキップ投票数**__', value='{}/3'.format(total_votes), inline=True)
				embed.set_footer(text='投票しました')
		else:
			embed.set_footer(text=ctx.message.author.name + ' は既に投票しています')
		await self.bot.send_message(ctx.message.channel, embed=embed)

	@commands.command(pass_context=True, no_pm=True, aliases = ['resume'])
	async def start(self, ctx):
		state = self.get_voice_state(ctx.message.server)
		embed = discord.Embed(title=BOT_NAME, color=0xff8080)
		if state.is_playing():
			player = state.player
			player.resume()
			embed.set_footer(text='再開しました')
		else:
			embed.set_footer(text='再生していません')
		await self.bot.send_message(ctx.message.channel, embed=embed)

	@commands.command(pass_context=True, no_pm=True, aliases = ['pause'])
	async def stop(self, ctx):
		state = self.get_voice_state(ctx.message.server)
		embed = discord.Embed(title=BOT_NAME, color=0xff8080)
		if state.is_playing():
			player = state.player
			player.pause()
			embed.set_footer(text='停止しました')
		else:
			embed.set_footer(text='再生していません')
		await self.bot.send_message(ctx.message.channel, embed=embed)

	@commands.command(pass_context=True, no_pm=True, aliases = ['list', 'pl'])
	async def playlist(self, ctx):
		player = self.get_player(ctx)
		upcoming = list(itertools.islice(player.queue._queue, 0, 5))
		fmt = '\n'.join(f'**`{_["title"]}`**' for _ in upcoming)
		embed = discord.Embed(title=f'Upcoming - Next {len(upcoming)}', description=fmt)

		await ctx.send_message(ctx.message.channel, embed=embed)

	@commands.command(pass_context=True, no_pm=True, aliases = ['n', 'np', 'playing'])
	async def now(self, ctx):
		state = self.get_voice_state(ctx.message.server)
		embed = discord.Embed(title=BOT_NAME, color=0xff8080)
		if not state.is_playing():
			embed.set_footer(text='現在何も再生していません')
		else:
			skip_count = len(state.skip_votes)
			embed.add_field(name='**＊** __**曲名 / 時間**__', value=state.current, inline=False)
			embed.add_field(name='**＊** __**スキップ投票数**__', value='{}/3'.format(skip_count), inline=False)
			embed.set_footer(text='再生中')
		await self.bot.send_message(ctx.message.channel, embed=embed)

def setup(bot):
	bot.add_cog(Music(bot))
	print('Music is loaded')
