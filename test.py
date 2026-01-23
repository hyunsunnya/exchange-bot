import os
import sys
import subprocess

# [추가] 라이브러리 자동 설치 로직
def install(package):
    # 사용자님의 요청대로 'python -m pip install' 방식을 사용합니다.
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import pandas_market_calendars as mcal
except ImportError:
    print("🚀 pandas_market_calendars 설치 중...")
    install('pandas_market_calendars')
    import pandas_market_calendars as mcal

import datetime
import asyncio
from telegram import Bot

# 환경 변수 로드
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# 한국 시간 설정 (UTC+9)
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

def check_if_market_opens_today():
    try:
        nyse = mcal.get_calendar('NYSE')
        today_str = now.strftime('%Y-%m-%d')
        # 해당 날짜의 스케줄 조회
        schedule = nyse.schedule(start_date=today_str, end_date=today_str)
        return schedule.empty  # 비어있으면 True(휴장), 있으면 False(영업)
    except Exception as e:
        print(f"달력 조회 에러: {e}")
        return False

async def main():
    print(f"🔍 [휴장 체크] 현재 한국 시간: {now.strftime('%Y-%m-%d %H:%M')}")
    
    is_holiday = check_if_market_opens_today()
    
    # [테스트용] 결과와 상관없이 로그는 항상 출력
    if is_holiday:
        status_msg = "😴 오늘은 미국 증시 휴장일입니다."
        if TOKEN and CHAT_ID:
            bot = Bot(token=TOKEN)
            msg = (f"📅 **미국 증시 휴장 안내**\n"
                   f"━━━━━━━━━━━━━━━\n"
                   f"오늘({now.strftime('%m/%d')}) 밤은 미국 시장이 **휴장**입니다.\n"
                   f"거래에 참고하세요! 💤")
            await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
            print("✅ 텔레그램 알림 전송 완료")
    else:
        status_msg = "📈 오늘은 미국 증시 영업일입니다."
        # 필요하다면 영업일일 때도 메시지를 보내게 수정 가능합니다.
    
    print(f"📊 최종 결과: {status_msg}")

if __name__ == "__main__":
    asyncio.run(main())
