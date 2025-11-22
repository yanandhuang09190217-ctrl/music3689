@bot.command()
async def play(ctx):
    # 使用者不在語音頻道
    if not ctx.author.voice:
        return await ctx.reply("⚠️ 你需要先加入語音頻道才能使用此功能！")

    ch = ctx.author.voice.channel

    # 取得 guild voice client（比 ctx.voice_client 更穩定）
    try:
        vc: wavelink.Player = ctx.guild.voice_client
    except:
        vc = None

    # 若未連接 → 連上
    if not vc:
        vc = await ch.connect(cls=wavelink.Player)
        await asyncio.sleep(0.5)  # 等待 player 初始化

    # 再確認一次 player 類型
    if not isinstance(vc, wavelink.Player):
        return await ctx.reply("❗ 音樂播放器未準備好，請再試一次。")

    # 詢問網址
    ask = await ctx.send("🎵 要播放的音樂網址是什麼呢？請在 60 秒內輸入。")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=60)
        query = msg.content.strip()
        try:
            await ask.delete()
            await msg.delete()
        except:
            pass
    except asyncio.TimeoutError:
        return await ctx.send("⏳ 已超過 60 秒未輸入，播放取消。")

    # 搜尋並播放
    try:
        track = await wavelink.YouTubeTrack.search(query=query, return_first=True)
    except Exception as e:
        return await ctx.send(f"❌ 搜尋錯誤：{e}")

    if not track:
        return await ctx.send("❌ 找不到這首歌，請確認網址或改用關鍵字。")

    try:
        await vc.play(track)
    except Exception as e:
        return await ctx.send(f"❌ 播放時錯誤：{e}")

    await ctx.send(f"▶ 正在播放：**{track.title}**")

    # 私訊通知
    try:
        await ctx.author.send(f"🎧 已成功開始播放音樂：**{track.title}**")
    except:
        await ctx.send("⚠️ 無法傳送私訊，但音樂已開始播放！")
