import os
import asyncio
import discord
from discord.ext import commands
import wavelink
from flask import Flask
from threading import Thread

# ============================
# Flask 讓 Render 保持運行
# ============================
app = Flask(__name__)

@app.route("/")
def home():
    return "Music Bot is running!"

def run_web():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ============================
# Discord Bot 設定
# ============================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 讀取 Render Environment Variables
TOKEN = os.getenv("TOKEN")

LAVALINK_HOST = os.getenv("LAVALINK_HOST")
LAVALINK_PORT = int(os.getenv("LAVALINK_PORT"))
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD")
LAVALINK_SECURE = os.getenv("LAVALINK_SECURE", "true").lower() == "true"


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    if not wavelink.Pool.nodes:
        await wavelink.Pool.connect(
            client=bot,
            nodes=[
                wavelink.Node(
                    uri=f"{'https' if LAVALINK_SECURE else 'http'}://{LAVALINK_HOST}:{LAVALINK_PORT}",
                    password=LAVALINK_PASSWORD
                )
            ]
        )

    print("🎵 Lavalink 已連接！")


# ============================
# 播放指令
# ============================
@bot.command()
async def play(ctx):
    if not ctx.author.voice:
        return await ctx.reply("⚠️ 請先加入語音頻道！")

    channel = ctx.author.voice.channel
    vc: wavelink.Player = ctx.guild.voice_client

    if not vc:
        vc = await channel.connect(cls=wavelink.Player)
        await asyncio.sleep(0.5)

    ask = await ctx.send("🎵 請輸入要播放的網址或關鍵字（60秒內）")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=60)
        query = msg.content
        await ask.delete()
        try:
            await msg.delete()
        except:
            pass
    except asyncio.TimeoutError:
        return await ctx.send("⏳ 超時，取消播放。")

    track = await wavelink.YouTubeTrack.search(query=query, return_first=True)

    if not track:
        return await ctx.send("❌ 找不到歌曲！")

    await vc.play(track)
    await ctx.send(f"▶ 正在播放：**{track.title}**")


# ============================
# 離開語音
# ============================
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 已離開語音頻道")
    else:
        await ctx.send("⚠️ 我目前沒有在語音頻道。")


# ============================
# 啟動
# ============================
if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run(TOKEN)
