import discord
from discord.ext import commands
import wavelink
import asyncio
import os

TOKEN = os.getenv("TOKEN")  # 讀取 Render 內建環境變數

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ 已登入：{bot.user}")

    if not wavelink.Pool.nodes:
        await wavelink.Pool.connect(
            client=bot,
            nodes=[
                wavelink.Node(
                    uri="http://lavalink:2333",
                    password="youshallnotpass"
                )
            ]
        )
        print("🔗 Lavalink 已連線")


@bot.command()
async def play(ctx):
    if not ctx.author.voice:
        return await ctx.reply("⚠️ 你必須先加入語音頻道！")

    channel = ctx.author.voice.channel

    vc: wavelink.Player = ctx.voice_client

    if not vc:
        vc = await channel.connect(cls=wavelink.Player)
        await asyncio.sleep(0.5)

    if not isinstance(vc, wavelink.Player):
        return await ctx.reply("❗ 音樂播放器尚未準備好，請重試。")

    ask = await ctx.send("🎵 要播放什麼？請輸入網址或關鍵字（60 秒內）。")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=60)
        query = msg.content.strip()
        await ask.delete()
        try:
            await msg.delete()
        except:
            pass
    except asyncio.TimeoutError:
        return await ctx.send("⏳ 超時未輸入，取消播放。")

    try:
        track = await wavelink.YouTubeTrack.search(query=query, return_first=True)
    except Exception as e:
        return await ctx.send(f"❌ 搜尋錯誤：{e}")

    if not track:
        return await ctx.send("❌ 找不到歌曲。")

    try:
        await vc.play(track)
    except Exception as e:
        return await ctx.send(f"❌ 播放失敗：{e}")

    await ctx.send(f"▶ 正在播放：**{track.title}**")

    try:
        await ctx.author.send(f"🎧 正在為你播放：**{track.title}**")
    except:
        pass


@bot.command()
async def leave(ctx):
    vc = ctx.voice_client
    if vc:
        await vc.disconnect()
        return await ctx.send("👋 已離開語音頻道")
    else:
        return await ctx.send("⚠️ 我不在語音頻道中。")


bot.run(DISCORD_TOKEN)
