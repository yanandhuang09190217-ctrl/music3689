import os
import asyncio
import discord
from discord.ext import commands
import wavelink
from flask import Flask
from threading import Thread

# -------------------
# Flask (keep-alive)
# -------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Music Bot is running on Render!", 200

def run_web():
    port = int(os.getenv("PORT", "10000"))
    # set debug=False in production
    app.run(host="0.0.0.0", port=port)

# -------------------
# Discord Bot settings
# -------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True         # 讀取成員狀態 (必要)
intents.voice_states = True    # 讀語音狀態 (必要)

bot = commands.Bot(command_prefix="!", intents=intents)

# Read TOKEN from Render environment
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("TOKEN environment variable not set")

# Use external cloud Lavalink (no Java required on Render)
# You can replace URI/password with another public Lavalink if you prefer
LAVALINK_URI = "https://lavalink.mariliuniverse.com:443"
LAVALINK_PASSWORD = "mariliu"

# Helper: ensure node connection (idempotent)
async def ensure_lavalink_connected():
    if not wavelink.Pool.is_connected():
        await wavelink.Pool.connect(
            client=bot,
            nodes=[
                # wavelink.Node takes uri like "https://host:443"
                wavelink.Node(uri=LAVALINK_URI, password=LAVALINK_PASSWORD)
            ],
        )

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (id: {bot.user.id})")
    try:
        await ensure_lavalink_connected()
        print("🔗 Lavalink connected")
    except Exception as e:
        print("❌ Lavalink connection failed:", e)


# --------------- Commands ---------------
@bot.command()
async def play(ctx):
    """!play -> ask for URL/keyword, then play via Lavalink"""
    author = ctx.author

    # 確認使用者在語音頻道
    if not author.voice or not author.voice.channel:
        await ctx.reply("⚠️ 請先加入語音頻道才能使用此功能！")
        return

    channel = author.voice.channel

    # 取得 guild player
    vc: wavelink.Player = ctx.guild.voice_client

    # connect if not connected
    if not vc:
        try:
            vc = await channel.connect(cls=wavelink.Player)
            await asyncio.sleep(0.5)  # let player initialize
        except Exception as e:
            await ctx.send(f"❌ 無法連接語音頻道：{e}")
            return

    # 再次檢查 player
    if not isinstance(vc, wavelink.Player):
        await ctx.reply("❗ 音樂播放器未準備好，請稍後再試。")
        return

    # 詢問歌曲 (文字頻道)
    ask_msg = await ctx.send("🎵 要播放的網址或關鍵字是？請在 60 秒內回覆。")

    def check(m):
        return m.author == author and m.channel == ctx.channel

    try:
        reply = await bot.wait_for("message", check=check, timeout=60)
        query = reply.content.strip()
        # 嘗試刪除問句與使用者回覆（若 bot 有權限）
        try:
            await ask_msg.delete()
            await reply.delete()
        except:
            pass
    except asyncio.TimeoutError:
        await ctx.send("⏳ 超時（60s），播放已取消。")
        return

    # 搜尋影片/曲目
    try:
        track = await wavelink.YouTubeTrack.search(query=query, return_first=True)
    except Exception as e:
        await ctx.send(f"❌ 搜尋歌曲時發生錯誤：{e}")
        return

    if not track:
        await ctx.send("❌ 找不到這首歌，請確認網址或改用關鍵字。")
        return

    # 播放
    try:
        await vc.play(track)
    except Exception as e:
        await ctx.send(f"❌ 播放發生錯誤：{e}")
        return

    await ctx.send(f"▶ 正在播放：**{track.title}**")

    # 私訊告知使用者
    try:
        await author.send(f"🎧 已開始播放：**{track.title}**")
    except:
        # 如果私訊失敗就忽略
        pass

@bot.command()
async def leave(ctx):
    """讓 bot 離開語音頻道"""
    vc = ctx.guild.voice_client
    if vc:
        await vc.disconnect()
        await ctx.send("👋 已離開語音頻道")
    else:
        await ctx.send("⚠️ 我目前不在語音頻道中。")

# ------------------- Start -------------------
if __name__ == "__main__":
    # start Flask in a thread so Render detects an open HTTP port
    Thread(target=run_web, daemon=True).start()

    # run bot (will block)
    bot.run(TOKEN)
