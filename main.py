import discord
from discord.ext import commands
import wavelink
import asyncio
import os
from flask import Flask
from threading import Thread

# ====== Web server for Render ======
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!", 200

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# ====== Discord Bot ======
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot 已登入：{bot.user}")

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
        print("Lavalink 已連線")


@bot.command()
async def play(ctx):
    if not ctx.author.voice:
        return await ctx.reply("⚠️ 你必須先加入語音頻道！")

    channel = ctx.author.voice.channel
    vc: wavelink.Player = ctx.voice_client

    if not vc:
        vc = await channel.connect(cls=wavelink.Player)
        await asyncio.sleep(0.5)

    ask = await ctx.send("🎵 要播放什麼音樂？請輸入網址或關鍵字（60 秒內）。")

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

    track = await wavelink.YouTubeTrack.search(query=query, return_first=True)
    if not track:
        return await ctx.send("❌ 找不到歌曲。")

    await vc.play(track)
    await ctx.send(f"▶ 正在播放：**{track.title}**")


@bot.command()
async def leave(ctx):
    vc = ctx.voice_client
    if vc:
        await vc.disconnect()
        return await ctx.send("👋 已離開語音頻道")
    else:
        return await ctx.send("⚠️ 我不在語音頻道內。")


# ====== Start web + bot ======
keep_alive()
bot.run(TOKEN)
