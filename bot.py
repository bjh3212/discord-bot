import discord
from discord.ext import commands
import asyncio
import random
import os
from datetime import datetime, timedelta
from typing import Optional
from database import Database
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import io

# 환경 변수에서 토큰 가져오기
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    TOKEN = "NEW_TOKEN"  # 여기에 봇 토큰을 입력하세요

# 관리자 ID 설정 (여러 관리자 가능)
ADMIN_IDS = os.getenv('ADMIN_IDS', '').split(',') if os.getenv('ADMIN_IDS') else []
ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS if id.strip()]

class StockBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        
        self.db = Database()
        self.stock_update_task = None
    
    async def setup_hook(self):
        # 슬래시 명령어 동기화
        await self.tree.sync()
        # 주식 가격 자동 업데이트 시작
        self.stock_update_task = asyncio.create_task(self.update_stock_prices())
    
    async def update_stock_prices(self):
        while not self.is_closed():
            try:
                stocks = self.db.get_all_stocks()
                for stock in stocks:
                    # 마지막 업데이트 시간 확인
                    if stock['last_update']:
                        last_update = datetime.fromisoformat(stock['last_update'].replace('Z', '+00:00'))
                        time_since_update = datetime.now() - last_update
                    else:
                        time_since_update = timedelta(seconds=stock['change_interval'] + 1)
                    
                    # 업데이트 주기가 지났으면 가격 변경
                    if time_since_update.total_seconds() >= stock['change_interval']:
                        change_rate = random.uniform(stock['min_change_rate'], stock['max_change_rate'])
                        # 상승/하락 50% 확률
                        if random.random() < 0.5:
                            change_rate = -change_rate
                        
                        new_price = int(stock['current_price'] * (1 + change_rate / 100))
                        new_price = max(1, new_price)  # 최소 1원
                        
                        self.db.update_stock_with_history(stock['name'], new_price)
                
                await asyncio.sleep(10)  # 10초마다 체크
            except Exception as e:
                print(f"주식 가격 업데이트 오류: {e}")
                await asyncio.sleep(10)
    
    def is_admin(self, user: discord.User) -> bool:
        return user.id in ADMIN_IDS or user.guild_permissions.administrator

bot = StockBot()

@bot.event
async def on_ready():
    print(f'{bot.user} 로그인 완료!')
    print(f'서버 수: {len(bot.guilds)}')

def validate_quantity(quantity: str) -> Optional[int]:
    """수량 검증: 정수여야 하고 양수여야 함"""
    try:
        qty = int(quantity)
        if qty <= 0:
            return None
        return qty
    except (ValueError, TypeError):
        return None

def validate_percentage(percent: str) -> Optional[float]:
    """퍼센트 검증: 숫자여야 함"""
    try:
        return float(percent)
    except (ValueError, TypeError):
        return None

def create_stock_chart(stock_name: str, price_history: list) -> discord.File:
    """주식 가격 그래프 생성"""
    if not price_history:
        return None
    
    # 데이터 준비 (시간 순서대로 정렬)
    prices = [entry['price'] for entry in reversed(price_history)]
    
    # 그래프 생성
    plt.figure(figsize=(12, 6))
    plt.plot(prices, linewidth=2, color='#3498db')
    plt.title(f'{stock_name} 주식 가격 차트', fontsize=16, fontweight='bold')
    plt.xlabel('시간 (최근 순)', fontsize=12)
    plt.ylabel('가격 (원)', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    
    # 가격 라벨 추가
    for i, price in enumerate(prices):
        if i % max(1, len(prices) // 10) == 0:  # 너무 많으면 건너뜀
            plt.annotate(f'{price:,}', (i, price), textcoords="offset points", xytext=(0,10), ha='center')
    
    plt.tight_layout()
    
    # 이미지로 변환
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
    img_buffer.seek(0)
    plt.close()
    
    return discord.File(img_buffer, filename=f'{stock_name}_chart.png')

# ========== 유저 명령어 ==========

@bot.tree.command(name="주식매수", description="주식을 구매합니다")
async def buy_stock(interaction: discord.Interaction, 이름: str, 수량: str):
    await interaction.response.defer()
    
    user_id = interaction.user.id
    quantity = validate_quantity(수량)
    
    if quantity is None:
        await interaction.followup.send("❌ 수량은 양의 정수여야 합니다.")
        return
    
    stock = bot.db.get_stock(이름)
    if not stock:
        await interaction.followup.send(f"❌ '{이름}' 주식을 찾을 수 없습니다.")
        return
    
    total_cost = stock['current_price'] * quantity
    user_money = bot.db.get_user_money(user_id)
    
    if user_money < total_cost:
        await interaction.followup.send(f"❌ 돈이 부족합니다. 필요 금액: {total_cost:,}원, 보유 금액: {user_money:,}원")
        return
    
    # 돈 차감 및 주식 추가
    if bot.db.update_user_money(user_id, -total_cost):
        bot.db.update_user_stock(user_id, 이름, quantity)
        bot.db.add_transaction(user_id, 이름, 'buy', quantity, stock['current_price'], total_cost)
        await interaction.followup.send(f"✅ {이름} 주식 {quantity}주를 {total_cost:,}원에 구매했습니다.")
    else:
        await interaction.followup.send("❌ 거래 실패: 잔액 부족")

@bot.tree.command(name="주식매도", description="주식을 판매합니다")
async def sell_stock(interaction: discord.Interaction, 이름: str, 수량: str):
    await interaction.response.defer()
    
    user_id = interaction.user.id
    quantity = validate_quantity(수량)
    
    if quantity is None:
        await interaction.followup.send("❌ 수량은 양의 정수여야 합니다.")
        return
    
    stock = bot.db.get_stock(이름)
    if not stock:
        await interaction.followup.send(f"❌ '{이름}' 주식을 찾을 수 없습니다.")
        return
    
    owned_quantity = bot.db.get_user_stock_quantity(user_id, 이름)
    
    if owned_quantity < quantity:
        await interaction.followup.send(f"❌ 보유한 주식이 부족합니다. 보유: {owned_quantity}주, 판매 시도: {quantity}주")
        return
    
    total_revenue = stock['current_price'] * quantity
    
    # 주식 차감 및 돈 추가
    if bot.db.update_user_stock(user_id, 이름, -quantity):
        bot.db.update_user_money(user_id, total_revenue)
        bot.db.add_transaction(user_id, 이름, 'sell', quantity, stock['current_price'], total_revenue)
        await interaction.followup.send(f"✅ {이름} 주식 {quantity}주를 {total_revenue:,}원에 판매했습니다.")
    else:
        await interaction.followup.send("❌ 거래 실패")

@bot.tree.command(name="시세", description="모든 주식의 현재 가격 및 정보를 확인합니다")
async def market_status(interaction: discord.Interaction):
    await interaction.response.defer()
    
    stocks = bot.db.get_all_stocks()
    
    if not stocks:
        await interaction.followup.send("❌ 등록된 주식이 없습니다.")
        return
    
    embed = discord.Embed(
        title="📈 주식 시세",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    
    for stock in stocks:
        # 확장 정보 가져오기
        stock_extended = bot.db.get_stock_extended(stock['name'])
        
        if stock_extended:
            # 초기가 대비 변동률
            initial_change = ((stock_extended['current_price'] - stock_extended['initial_price']) / stock_extended['initial_price']) * 100
            
            # 이전 가격 대비 변동률
            if stock_extended['previous_price'] > 0:
                previous_change = ((stock_extended['current_price'] - stock_extended['previous_price']) / stock_extended['previous_price']) * 100
            else:
                previous_change = 0
            
            emoji = "📈" if initial_change >= 0 else "📉"
            color = "🟢" if initial_change >= 0 else "🔴"
            prev_color = "🟢" if previous_change >= 0 else "🔴"
            
            embed.add_field(
                name=f"{emoji} {stock['name']}",
                value=f"""
                **현재가:** {stock_extended['current_price']:,}원
                **초기가 대비:** {color} {initial_change:+.2f}%
                **이전가 대비:** {prev_color} {previous_change:+.2f}%
                **초기가:** {stock_extended['initial_price']:,}원
                **최고가:** {stock_extended['high_price']:,}원
                **최저가:** {stock_extended['low_price']:,}원
                **거래량:** {stock_extended['volume']:,}
                """,
                inline=False
            )
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="내프로필", description="내 자산과 보유 주식을 확인합니다")
async def my_profile(interaction: discord.Interaction):
    await interaction.response.defer()
    
    user_id = interaction.user.id
    money = bot.db.get_user_money(user_id)
    stocks = bot.db.get_user_stocks(user_id)
    
    embed = discord.Embed(
        title=f"💰 {interaction.user.display_name}의 프로필",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="💵 보유 현금",
        value=f"{money:,}원",
        inline=False
    )
    
    if stocks:
        stock_list = []
        total_stock_value = 0
        for stock_name, quantity in stocks.items():
            stock = bot.db.get_stock(stock_name)
            if stock:
                value = stock['current_price'] * quantity
                total_stock_value += value
                change_percent = ((stock['current_price'] - stock['initial_price']) / stock['initial_price']) * 100
                stock_list.append(f"• {stock_name}: {quantity}주 ({value:,}원, {change_percent:+.2f}%)")
        
        embed.add_field(
            name="📊 보유 주식",
            value="\n".join(stock_list),
            inline=False
        )
        
        embed.add_field(
            name="💎 총 자산",
            value=f"{money + total_stock_value:,}원 (현금: {money:,}원 + 주식: {total_stock_value:,}원)",
            inline=False
        )
    else:
        embed.add_field(
            name="📊 보유 주식",
            value="보유한 주식이 없습니다.",
            inline=False
        )
        
        embed.add_field(
            name="💎 총 자산",
            value=f"{money:,}원",
            inline=False
        )
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="주식그래프", description="주식 가격 그래프를 확인합니다")
async def stock_chart(interaction: discord.Interaction, 이름: str):
    await interaction.response.defer()
    
    stock = bot.db.get_stock_extended(이름)
    if not stock:
        await interaction.followup.send(f"❌ '{이름}' 주식을 찾을 수 없습니다.")
        return
    
    # 가격 히스토리 가져오기
    price_history = bot.db.get_price_history(이름, limit=50)
    
    if not price_history:
        await interaction.followup.send(f"❌ '{이름}' 주식의 가격 히스토리가 없습니다.")
        return
    
    # 그래프 생성
    chart_file = create_stock_chart(이름, price_history)
    
    if chart_file:
        await interaction.followup.send(file=chart_file)
    else:
        await interaction.followup.send("❌ 그래프 생성 실패")

@bot.tree.command(name="거래내역", description="내 거래 내역을 확인합니다")
async def transaction_history(interaction: discord.Interaction):
    await interaction.response.defer()
    
    user_id = interaction.user.id
    transactions = bot.db.get_user_transactions(user_id, limit=20)
    
    if not transactions:
        await interaction.followup.send("❌ 거래 내역이 없습니다.")
        return
    
    embed = discord.Embed(
        title=f"📋 {interaction.user.display_name}의 거래 내역",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    for tx in transactions:
        tx_type_emoji = "🟢" if tx['transaction_type'] == 'buy' else "🔴"
        tx_type_text = "매수" if tx['transaction_type'] == 'buy' else "매도"
        
        embed.add_field(
            name=f"{tx_type_emoji} {tx['stock_name']} - {tx_type_text}",
            value=f"""
            **수량:** {tx['quantity']:,}주
            **가격:** {tx['price']:,}원
            **총액:** {tx['total_amount']:,}원
            **시간:** {tx['timestamp']}
            """,
            inline=False
        )
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="상세변동률", description="주식의 상세 변동률을 시간대별로 확인합니다")
async def detailed_change_rate(interaction: discord.Interaction, 이름: str, 시간대: str = "1시간"):
    await interaction.response.defer()
    
    stock = bot.db.get_stock_extended(이름)
    if not stock:
        await interaction.followup.send(f"❌ '{이름}' 주식을 찾을 수 없습니다.")
        return
    
    # 시간대 파싱
    time_map = {
        "1분": 1,
        "5분": 5,
        "10분": 10,
        "30분": 30,
        "1시간": 60,
        "6시간": 360,
        "12시간": 720,
        "1일": 1440,
        "1주": 10080
    }
    
    minutes = time_map.get(시간대, 60)
    
    # 가격 히스토리 가져오기
    price_history = bot.db.get_price_history(이름, limit=1000)
    
    if not price_history or len(price_history) < 2:
        await interaction.followup.send(f"❌ '{이름}' 주식의 가격 히스토리가 부족합니다.")
        return
    
    # 시간대별 필터링
    cutoff_time = datetime.now() - timedelta(minutes=minutes)
    filtered_history = [
        entry for entry in price_history
        if datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00')) >= cutoff_time
    ]
    
    if len(filtered_history) < 2:
        await interaction.followup.send(f"❌ {시간대} 동안의 가격 히스토리가 부족합니다.")
        return
    
    # 변동률 계산
    oldest_price = filtered_history[-1]['price']
    newest_price = filtered_history[0]['price']
    change_percent = ((newest_price - oldest_price) / oldest_price) * 100
    
    # 최고가/최저가
    prices = [entry['price'] for entry in filtered_history]
    period_high = max(prices)
    period_low = min(prices)
    
    emoji = "📈" if change_percent >= 0 else "📉"
    color = "🟢" if change_percent >= 0 else "🔴"
    
    embed = discord.Embed(
        title=f"{emoji} {이름} - {시간대} 변동률",
        color=discord.Color.green() if change_percent >= 0 else discord.Color.red(),
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="변동률",
        value=f"{color} {change_percent:+.2f}%",
        inline=True
    )
    
    embed.add_field(
        name="시작가",
        value=f"{oldest_price:,}원",
        inline=True
    )
    
    embed.add_field(
        name="종료가",
        value=f"{newest_price:,}원",
        inline=True
    )
    
    embed.add_field(
        name="기간 최고가",
        value=f"{period_high:,}원",
        inline=True
    )
    
    embed.add_field(
        name="기간 최저가",
        value=f"{period_low:,}원",
        inline=True
    )
    
    embed.add_field(
        name="데이터 포인트",
        value=f"{len(filtered_history)}개",
        inline=True
    )
    
    await interaction.followup.send(embed=embed)

# ========== 관리자 명령어 ==========

@bot.tree.command(name="주식제작", description="새로운 주식을 생성합니다 (관리자 전용)")
async def create_stock(
    interaction: discord.Interaction, 
    이름: str, 
    주당가격: str, 
    최저상승률: str, 
    최대상승률: str, 
    시세변화주기: str
):
    if not bot.is_admin(interaction.user):
        await interaction.response.send_message("❌ 이 명령어는 관리자만 사용할 수 있습니다.", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    try:
        price = int(주당가격)
        min_change = float(최저상승률)
        max_change = float(최대상승률)
        interval = int(시세변화주기)
        
        if price <= 0:
            await interaction.followup.send("❌ 주당 가격은 양수여야 합니다.")
            return
        
        if max_change < 0:
            await interaction.followup.send("❌ 최대상승률은 양수여야 합니다.")
            return
        
        if min_change > max_change:
            await interaction.followup.send("❌ 최저상승률은 최대상승률보다 작거나 같아야 합니다.")
            return
        
        if interval <= 0:
            await interaction.followup.send("❌ 시세변화주기는 양수여야 합니다.")
            return
        
        if bot.db.create_stock(이름, price, min_change, max_change, interval):
            await interaction.followup.send(f"✅ '{이름}' 주식이 생성되었습니다.\n가격: {price:,}원\n변동범위: {min_change}% ~ {max_change}%\n변화주기: {interval}초")
        else:
            await interaction.followup.send(f"❌ '{이름}' 주식이 이미 존재합니다.")
            
    except ValueError:
        await interaction.followup.send("❌ 잘못된 입력 형식입니다. 가격과 주기는 정수, 상승률은 실수여야 합니다.")

@bot.tree.command(name="주식삭제", description="주식을 삭제합니다 (관리자 전용)")
async def delete_stock(interaction: discord.Interaction, 이름: str):
    if not bot.is_admin(interaction.user):
        await interaction.response.send_message("❌ 이 명령어는 관리자만 사용할 수 있습니다.", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    if bot.db.delete_stock(이름):
        await interaction.followup.send(f"✅ '{이름}' 주식이 삭제되었습니다.")
    else:
        await interaction.followup.send(f"❌ '{이름}' 주식을 찾을 수 없습니다.")

@bot.tree.command(name="주식변동", description="주식 가격을 즉시 변경합니다 (관리자 전용)")
async def fluctuate_stock(interaction: discord.Interaction, 이름: str, 퍼센트: str):
    if not bot.is_admin(interaction.user):
        await interaction.response.send_message("❌ 이 명령어는 관리자만 사용할 수 있습니다.", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    percent = validate_percentage(퍼센트)
    
    if percent is None:
        await interaction.followup.send("❌ 퍼센트는 숫자여야 합니다.")
        return
    
    stock = bot.db.get_stock(이름)
    if not stock:
        await interaction.followup.send(f"❌ '{이름}' 주식을 찾을 수 없습니다.")
        return
    
    new_price = int(stock['current_price'] * (1 + percent / 100))
    new_price = max(1, new_price)  # 최소 1원
    
    bot.db.update_stock_price(이름, new_price)
    
    change_emoji = "📈" if percent >= 0 else "📉"
    await interaction.followup.send(f"✅ {이름} 주식 가격이 {percent:+.2f}% 변동되었습니다.\n{change_emoji} 이전가: {stock['current_price']:,}원 → 새로운가: {new_price:,}원")

if __name__ == "__main__":
    bot.run(TOKEN)
