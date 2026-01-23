import os
import datetime
import asyncio
import pandas_market_calendars as mcal
from telegram import Bot

# 환경 변수 로드
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

async def check_us_market():
    nyse = mcal.get_calendar('NYSE')
    now = datetime.datetime.now() + datetime.timedelta(hours=9)
    today_str = now.strftime('%Y-%m-%d')
    
    print(f"🔍 확인 날짜: {today_str}")
    schedule = nyse.schedule(start_date=today_str, end_date=today_str)
    
    if schedule.empty:
        result_msg = f"📉 오늘은 미국 증시 **휴장일**입니다. ({today_str})"
    else:
        result_msg = f"📈 오늘은 미국 증시 **정상 영업일**입니다. ({today_str})"

    if not TOKEN or not CHAT_ID:
        print("❌ 환경변수 누락"); return

    try:
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=f"🔔 **미국 증시 알림**\n\n{result_msg}", parse_mode='Markdown')
        print("✅ 전송 성공")
    except Exception as e:
        print(f"❌ 전송 실패: {e}")

if __name__ == "__main__":
    asyncio.run(check_us_market())
