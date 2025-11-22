from flask import Flask
from threading import Thread
import os
import discord
from discord.ext import commands
import asyncio

# ============= Flask (保持 Web Service 運作) =============

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_web():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ============= Discord Bot 設定 =============

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("TOKEN")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")


if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.run(TOKEN)
