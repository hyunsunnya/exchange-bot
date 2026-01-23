import requests
import datetime
import os
import sys
import asyncio
from telegram import Bot

# --- 설정 및 환경 변수 ---
SERVICE_KEY = os.environ.get('KMA_API_KEY')
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# 한국 시간 설정
now = datetime.datetime.now() + datetime.timedelta(hours=9)

# 지역 설정 (수원 기준)
REGION_NAME = "수원시 영통구"; NX, NY = 61, 120

async def main():
    if not all([SERVICE_KEY, TOKEN, CHAT_ID]):
        print("❌ 환경변수 확인 필요"); return

    print(f"🚀 날씨 데이터 수집 시작... ({now.strftime('%H:%M')})")

    # 1. 실시간 기온 가져오기
    url = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    base_dt = now - datetime.timedelta(hours=1)
    params = {
        'serviceKey': SERVICE_KEY, 'pageNo': '1', 'numOfRows': '10', 'dataType': 'JSON',
        'base_date': base_dt.strftime('%Y%m%d'),
        'base_time': base_dt.strftime('%H') + "00",
        'nx': NX, 'ny': NY
    }
    
    try:
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        items = data['response']['body']['items']['item']
        real_temp = next(item['obsrValue'] for item in items if item['category'] == 'T1H')
        
        msg = (f"🌈 **오늘의 날씨 테스트**\n"
               f"📍 `{REGION_NAME}`\n"
               f"🌡️ **현재 기온:** `{real_temp}°C`\n"
               f"✨ 정상적으로 데이터를 가져왔습니다!")

        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
        print(f"✅ 날씨 전송 완료: {real_temp}도")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(main())
