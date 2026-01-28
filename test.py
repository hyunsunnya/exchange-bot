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

# 시간 설정 (KST)
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# 1. 주말 체크
if now.weekday() >= 5:
    sys.exit()

# 2. 공휴일 체크 (2026년 기준)
korea_holidays = ["2026-01-01", "2026-02-16", "2026-02-17", "2026-02-18", "2026-03-01", "2026-03-02", "2026-05-05", "2026-06-06", "2026-08-15", "2026-09-24", "2026-09-25", "2026-09-26", "2026-10-03", "2026-10-09", "2026-12-25"]
if now.strftime('%Y-%m-%d') in korea_holidays:
    sys.exit()


async def get_naver_exchange_rate(code):
    url = f"https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd={code}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        current_price = float(soup.select_one(".value").text.replace(",", ""))
        change_element = soup.select_one(".change").text.strip().split()
        change_amt = float(change_element[0].replace(",", ""))
        
        direction = soup.select_one(".no_today .blind").text
        if "하락" in direction:
            change_amt = -change_amt
            
        change_rate = float(soup.select_one(".point_status").text.strip().replace("%", ""))
        if "하락" in direction:
            change_rate = -change_rate

        return {'current': current_price, 'change_amt': change_amt, 'change_rate': change_rate}
    except Exception as e:
        print(f"Error fetching {code}: {e}")
        return None

async def main():
    if not TOKEN or not CHAT_ID: return

    usd = await get_naver_exchange_rate("FX_USDKRW")
    jpy = await get_naver_exchange_rate("FX_JPYKRW")
    
    msg_items = []
    if usd:
        mark = "🔺" if usd['change_rate'] > 0 else "🔻"
        msg_items.append(f"💵 **달러(USD/KRW)**\n  • 현재가: `{usd['current']:,.2f}원`\n  • 전일비: {mark} `{usd['change_amt']:+.2f}원` ({usd['change_rate']:+.2f}%)")
    
    if jpy:
        mark = "🔺" if jpy['change_rate'] > 0 else "🔻"
        msg_items.append(f"💴 **엔화(JPY/KRW 100)**\n  • 현재가: `{jpy['current']:,.2f}원`\n  • 전일비: {mark} `{jpy['change_amt']:+.2f}원` ({jpy['change_rate']:+.2f}%)")
    
    if msg_items:
        final_msg = f"📊 **데일리 환율 정보 (네이버)**\n📅 기준 시간: {now.strftime('%m/%d %H:%M')}\n━━━━━━━━━━━━━━━\n\n" + "\n\n".join(msg_items)
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=final_msg, parse_mode='Markdown')

if __name__ == "__main__":
    asyncio.run(main())
