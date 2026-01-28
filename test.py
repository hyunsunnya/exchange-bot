import requests
from bs4 import BeautifulSoup
import asyncio
import os
import datetime
import sys
from telegram import Bot

# GitHub Secrets
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# [시간 설정] 한국 시간 기준 (UTC+9)
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# --- 주말 및 공휴일 체크 로직 ---
if now.weekday() >= 5:
    sys.exit()

korea_holidays = ["2026-01-01", "2026-02-16", "2026-02-17", "2026-02-18", "2026-03-01", "2026-03-02", "2026-05-05", "2026-06-06", "2026-08-15", "2026-09-24", "2026-09-25", "2026-09-26", "2026-10-03", "2026-10-09", "2026-12-25"]
if now.strftime('%Y-%m-%d') in korea_holidays:
    sys.exit()

# 실행 시간 제한 (테스트 시 주석 처리 가능)
if not (now.hour == 10 and 0 <= now.minute <= 30):
    # print(f"현재 {now.strftime('%H:%M')} - 실행 시간이 아닙니다.")
    sys.exit()

async def get_google_exchange(ticker):
    """구글 파이낸스에서 전일비가 포함된 정확한 환율 데이터를 가져옵니다."""
    url = f"https://www.google.com/finance/quote/{ticker}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 구글 파이낸스 특유의 클래스 구조를 활용해 데이터를 정확히 추출합니다.
        price_tag = soup.select_one('div[class*="YMlS1d"]') # 현재가
        change_tag = soup.select_one('div[class*="Jw7XHd"]') # 전일비 정보
        
        if not price_tag or not change_tag:
            return None
            
        current_price = float(price_tag.text.replace(',', ''))
        
        # change_text 예: "+1.50 (0.11%)" 또는 "-2.30 (0.18%)"
        change_text = change_tag.text.replace('+', '').replace('%', '')
        parts = change_text.split()
        change_amt = float(parts[0].replace(',', '')) # 전일비 금액
        change_rate = float(parts[1].replace('(', '').replace(')', '')) # 증감률
        
        return {'current': current_price, 'change_amt': change_amt, 'change_rate': change_rate}
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

async def main():
    if not TOKEN or not CHAT_ID: return

    # 구글용 티커로 데이터 요청
    usd = await get_google_exchange("USD-KRW")
    jpy_raw = await get_google_exchange("JPY-KRW")
    
    msg_items = []
    
    if usd:
        mark = "🔺" if usd['change_rate'] > 0 else "🔻"
        if usd['change_rate'] == 0: mark = "━"
        msg_items.append(
            f"💵 **달러(USD/KRW)**\n"
            f"  • 현재가: `{usd['current']:,.2f}원`\n"
            f"  • 전일비: {mark} `{usd['change_amt']:+.2f}원` ({usd['change_rate']:+.2f}%)"
        )

    if jpy_raw:
        # 구글은 1엔 기준이므로 100엔으로 변환
        jpy_100 = jpy_raw['current'] * 100
        jpy_amt = jpy_raw['change_amt'] * 100
        mark = "🔺" if jpy_raw['change_rate'] > 0 else "🔻"
        if jpy_raw['change_rate'] == 0: mark = "━"
        msg_items.append(
            f"💴 **엔화(JPY/KRW 100)**\n"
            f"  • 현재가: `{jpy_100:,.2f}원`\n"
            f"  • 전일비: {mark} `{jpy_amt:+.2f}원` ({jpy_raw['change_rate']:+.2f}%)"
        )
    
    if msg_items:
        final_msg = f"📊 **데일리 환율 정보 (Google)**\n📅 {now.strftime('%m/%d %H:%M')}\n━━━━━━━━━━━━━━━\n\n" + "\n\n".join(msg_items)
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=final_msg, parse_mode='Markdown')
        print("✅ 정확한 환율 정보 전송 완료")

if __name__ == "__main__":
    asyncio.run(main())
