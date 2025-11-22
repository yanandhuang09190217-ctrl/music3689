import os
import asyncio
import discord
from discord.ext import commands
import wavelink
from flask import Flask
from threading import Thread

# ============================
# Flask 讓 Render 保持運作
# ============================
app = Flask(__name__)

@app.route("/")
def home():
    return "Music Bot is running on Render!"

def run_web():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ============================
# Discord Bot 設定
# ============================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("TOKEN")

# 雲端 Lavalink 設定（已幫你填好）
LAVALINK_URI = "https://lavalink.mariliuniverse.com:443"
LAVALINK_PASSWORD = "mariliu"


@bot.event
async def on_ready():
    print(f"✅ 已登入：{bot.user}")

    if not wavelink.Pool.is_connected():
        await wavelink.Pool.connect(
            client=bot,
            nodes=[
                wavelink.Node(
                    uri=LAVALINK_URI,
                    password=LAVALINK_PASSWORD
                )
            ]
        )
        print("🔗 外部 Lavalink 已連線")


# ============================
# 播放
# ============================
@bot.command()
async def play(ctx):
    if not ctx.author.voice:
        return await ctx.reply("⚠️ 你必須先加入語音頻道！")

    channel = ctx.au
