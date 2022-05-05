import asyncio
import youtube_dl
import discord
from discord.ext import commands

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ""

# TODO: rewrite
ytdl_format_options = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # Bind to ipv4 since ipv6 addresses cause issues at certain times
}

ffmpeg_options = {"options": "-vn"}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.1):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get("title")
        self.duration = data.get("duration")
        self.url = data.get("webpage_url")

    # TODO: Support serach
    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if "entries" in data:
            # Takes the first item from a playlist
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):
    song_queue = []
    current_song = None
    loop_song = False

    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""
        # TODO Only first "play-user" can move bot when playing
        author_voice = ctx.author.voice.channel
        if author_voice is None:
            await ctx.respond(f"You arent in any voice-channel")
        if ctx.voice_client is None:
            await author_voice.connect()
        else:
            await ctx.voice_client.move_to(author_voice)
        await ctx.respond(f"Connected", delete_after=0)

    @discord.slash_command(name="p")
    async def play_other_old(self, ctx, *, query):
        """Plays a file from the local filesystem"""

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
        ctx.voice_client.play(source, after=lambda e: print(f"Player error: {e}") if e else None)

        await ctx.send(f"Now playing: {query}")

    @discord.slash_command()
    async def play(self, ctx, url: str):
        """Playes song from an url"""
        async with ctx.typing():
            requested_song = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            if self.current_song is None:
                self.song_queue.append(requested_song)
                self.current_song = requested_song
                ctx.voice_client.play(self.song_queue.pop(0),
                                      after=lambda e: print(f"Player error: {e}") if e else self.play_next(ctx))
                await ctx.respond(f"Now playing: {requested_song.title}")
            else:
                self.song_queue.append(requested_song)
                await ctx.respond("A song is already playing.\nSong was added to the queue")

    def play_next(self, ctx):
        # ctx.voice_client.stop() is this necessary?
        if not self.loop_song:
            if len(self.song_queue) > 0:
                self.current_song = self.song_queue.pop(0)
            else:
                self.song_queue.clear()
                self.current_song = None
                self.loop_song = False
                ctx.voice_client.disconnect()
        ctx.voice_client.play(self.current_song,
                              after=lambda e: print(f"Player error: {e}") if e else self.play_next(ctx))

    # TODO: same as play-command?
    @discord.slash_command(name="add-song")
    async def song_add(self, ctx, url: str):
        self.song_queue.append(await YTDLSource.from_url(url, loop=self.bot.loop, stream=True))
        await ctx.respond("Song was added to the queue")

    @discord.slash_command()
    async def queue(self, ctx):
        """Displays the current songs in queue"""
        text = "\n".join([song.title for song in self.song_queue])
        await ctx.respond(self.current_song.title + "\n" + text)

    @discord.slash_command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""
        if ctx.voice_client is None:
            return await ctx.respond("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.respond(f"Changed volume to {volume}%")

    @discord.slash_command()
    async def skip(self, ctx):
        """Skips the current song even if looping"""
        self.loop_song = False
        await ctx.voice_client.stop()  # is this necessary?
        await ctx.voice_client.play(self.song_queue.pop(0),
                                    after=lambda e: print(f"Player error: {e}") if e else self.play_next(ctx))
        await ctx.respond("Now playing here goes song text")

    @discord.slash_command()
    async def loop(self, ctx):
        """Toggles looping of the current song"""
        if self.loop_song is not None:
            if not self.loop_song:
                self.loop_song = True
                await ctx.respond("The current song is looping")
            else:
                self.loop_song = False
                await ctx.respond("The current song is not looping")
        else:
            await ctx.respond("No song curretnly playing")

    @discord.slash_command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""
        self.song_queue.clear()
        self.current_song = None
        self.loop_song = False
        await ctx.voice_client.disconnect()
        await ctx.respond("leaving")

    @discord.slash_command()
    async def pause(self, ctx):
        """Pauses the song"""
        await ctx.respond("Paused")
        ctx.voice_client.pause()

    @discord.slash_command()
    async def resume(self, ctx):
        """Resumes the song"""
        await ctx.respond("Resumed")
        ctx.voice_client.resume()

    # TODO: rework logic
    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()