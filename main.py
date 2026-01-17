import discord
from discord import ui, app_commands
from discord.ext import commands
import wavelink
import os

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

import discord
from discord import ui, app_commands
from discord.ext import commands
import wavelink
import os
from aiohttp import web # 웹 서버용 라이브러리

# --- 1. Render 잠자기 방지를 위한 미니 웹 서버 ---
async def handle(request):
    return web.Response(text="Bot is Running!")

async def start_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000) # Render는 보통 10000 포트를 씁니다
    await site.start()

# --- 2. 봇 설정 및 메인 로직 ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # 웹 서버 시작
        self.loop.create_task(start_server())
        
        # 공개용 Lavalink 서버 정보 (주소와 비밀번호 확인!)
        # 아래 주소 중 하나를 골라서 넣어보세요.
        node = wavelink.Node(
            uri="https://lavalink.lexis.host:443", # https와 443 포트 사용
            password="lexishost"
        )
        
        await wavelink.Pool.connect(nodes=[node], client=self)
        print("✅ 공개 Lavalink 서버 연결 성공!")

        self.add_view(MusicControlView())
        await self.tree.sync()

bot = MyBot()

# --- 3. 인터페이스 (자판기 버튼) ---
class MusicControlView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="노래 검색 & 신청", style=discord.ButtonStyle.success, emoji="🔍", custom_id="persistent:search")
    async def search(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(SearchModal())

    @ui.button(label="일시정지/재생", style=discord.ButtonStyle.primary, emoji="⏯️", custom_id="persistent:pause")
    async def pause_resume(self, interaction: discord.Interaction, button: ui.Button):
        vc: wavelink.Player = interaction.guild.voice_client
        if not vc: return await interaction.response.send_message("현재 재생 중인 음악이 없어요!", ephemeral=True)
        await vc.pause(not vc.paused)
        await interaction.response.send_message(f"✅ {'일시정지' if vc.paused else '다시 재생'}!", ephemeral=True)

    @ui.button(label="정지 및 퇴장", style=discord.ButtonStyle.danger, emoji="⏹️", custom_id="persistent:stop")
    async def stop(self, interaction: discord.Interaction, button: ui.Button):
        vc: wavelink.Player = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            await interaction.response.send_message("⏹️ 정지되었습니다.", ephemeral=True)

# --- 4. 검색창 (모달) ---
class SearchModal(ui.Modal, title="🎵 노래 자판기"):
    song_name = ui.TextInput(label="곡 제목", placeholder="듣고 싶은 노래를 입력하세요")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.voice:
            return await interaction.followup.send("음성 채널에 먼저 들어가주세요!")

        tracks = await wavelink.Playable.search(self.song_name.value)
        if not tracks: return await interaction.followup.send("결과가 없어요.")

        view = ui.View(timeout=60)
        select = ui.Select(placeholder="목록에서 곡을 골라주세요")
        
        for i, track in enumerate(tracks[:10]):
            select.add_option(label=track.title[:100], value=str(i), description=track.author[:100])

        async def callback(inter: discord.Interaction):
            track = tracks[int(select.values[0])]
            vc: wavelink.Player = inter.guild.voice_client or await inter.user.voice.channel.connect(cls=wavelink.Player)
            await vc.play(track)
            
            embed = discord.Embed(title="💿 재생 시작", description=f"**{track.title}**", color=0x00ff00)
            if track.artwork: embed.set_thumbnail(url=track.artwork)
            await inter.response.send_message(embed=embed)

        select.callback = callback
        view.add_item(select)
        await interaction.followup.send("원하시는 곡을 선택하세요:", view=view, ephemeral=True)

@bot.tree.command(name="음악세팅", description="설명이 포함된 음악 자판기를 생성합니다.")
@app_commands.checks.has_permissions(administrator=True)
async def music_setup(interaction: discord.Interaction):
    # 1. 엠베드 디자인 구성
    embed = discord.Embed(
        title="🎵 고음질 음악 자판기 (Music Vending Machine)",
        description=(
            "이곳은 우리 서버 전용 음악 신청 공간입니다! 봇에게 명령어를 입력할 필요 없이 아래 버튼들로 간편하게 음악을 감상해보세요.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "### 📖 사용 방법\n"
            "1. **음성 채널 입장**: 노래를 듣고 싶은 음성 채널에 먼저 들어가주세요.\n"
            "2. **🔍 노래 검색**: 버튼을 누르고 창이 뜨면 제목을 입력해주세요.\n"
            "3. **곡 선택**: 검색 결과 목록에서 원하는 곡을 고르면 끝!\n"
            "4. **조작**: 재생 중에 일시정지나 정지 버튼을 자유롭게 사용하세요.\n\n"
            "### ⚙️ 시스템 정보\n"
            "• **음질**: 320kbps High-Quality (Lavalink Engine)\n"
            "• **지원**: 유튜브, 스포티파이, 사운드클라우드\n"
            "• **상태**: 24시간 가동 중 🟢\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0x5865F2 # 디스코드 공식 블루 색상
    )
    
    # 2. 이미지 및 푸터 설정
    embed.set_image(url="https://i.imgur.com/8N4N4Rj.gif") # 음악 비트 GIF
    embed.set_footer(text="💡 팁: 노래가 끊긴다면 음성 채널의 비트레이트 설정을 확인해주세요.")
    
    # 3. 버튼과 함께 전송
    await interaction.response.send_message(embed=embed, view=MusicControlView())

async def setup_hook(self):
        # 웹 서버 시작
        self.loop.create_task(start_server())
        
        # Lavalink 연결 시도 로직
        nodes = [wavelink.Node(uri="http://127.0.0.1:2333", password="youshallnotpass")]
        
        # 연결될 때까지 10초마다 재시도 (최대 10번)
        for i in range(1, 11):
            try:
                await wavelink.Pool.connect(nodes=nodes, client=self)
                print("✅ [성공] Lavalink 서버에 연결되었습니다!")
                break
            except Exception as e:
                print(f"⚠️ [대기] Lavalink 서버가 아직 준비되지 않았습니다. 재시도 중... ({i}/10)")
                await asyncio.sleep(10) # 10초 대기

        self.add_view(MusicControlView())
        await self.tree.sync()

bot.run(os.getenv('BOT_TOKEN'))


