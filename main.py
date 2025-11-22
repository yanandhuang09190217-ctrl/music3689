import os
import threading
from flask import Flask
import discord
from discord.ext import commands
import wavelink
import asyncio

# Environment
TOKEN = os.getenv("DISCORD_TOKEN")
LAVALINK_HOST = os.getenv("LAVALINK_HOST", "lavalink.botsfordiscord.com")
LAVALINK_PORT = int(os.getenv("LAVALINK_PORT", "443"))
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")
LAVALINK_SECURE = os.getenv("LAVALINK_SECURE", "true").lower() in ("1", "true", "yes")

# Flask web server
app = Flask(__name__)

@app.route("/")
def home():
    return "Music bot is running"

def run_web():
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)


# Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    try:
        await wavelink.NodePool.create_node(
            bot=bot,
            host=LAVALINK_HOST,
            port=LAVALINK_PORT,
            password=LAVALINK_PASSWORD,
            secure=LAVALINK_SECURE
        )
        print("Lavalink node connected.")

    except Exception as e:
        print("Lavalink failed:", e)


@bot.command()
async def play(ctx):

    # 使用者不在語音頻道
    if not ctx.author.voice:
        return await ctx.reply("⚠️ 你需要先加入語音頻道！")

    ch = ctx.author.voice.channel

    # 正確取得 wavelink Player
    try:
        vc: wavelink.Player = ctx.guild.voice_client
    except:
        vc = None

    # 若未連接 → 連上去
    if not vc:
        vc = await ch.connect(cls=wavelink.Player)
        await asyncio.sleep(0.5)  # 等待 Lavalink 設置完成

    # 做一個保險，多檢查一次
    if not isinstance(vc, wavelink.Player):
        return await ctx.reply("❗ 音樂播放器未準備好，請再試一次。")

    # 文字頻道詢問音樂網址
    ask = await ctx.send("🎵 要播放的音樂網址？請在 60 秒內輸入。")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=60)
        query = msg.content.strip()
    except asyncio.TimeoutError:
        return await ctx.send("⏳ 已超過 60 秒未輸入，取消播放。")

    # 搜尋音樂
    try:
        track = await wavelink.YouTubeTrack.search(query=query, return_first=True)
    except Exception as e:
        return await ctx.send(f"❌ 搜尋錯誤：{e}")

    if not track:
        return await ctx.send("❌ 找不到這首歌！")

    # 播放
    try:
        await vc.play(track)
    except Exception as e:
        return await ctx.send(f"❌ 播放時錯誤：{e}")

    await ctx.send(f"▶ 正在播放：**{track.title}**")


if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.run(TOKEN)
