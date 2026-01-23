import requests
import datetime
import os
import sys
import asyncio
from telegram import Bot

# --- 환경 변수 체크 ---
SERVICE_KEY = os.environ.get('KMA_API_KEY')
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

print("--- [Step 1] 환경 변수 로드 확인 ---")
print(f"KMA_API_KEY 존재 여부: {'✅ 있음' if SERVICE_KEY else '❌ 없음'}")
print(f"TELEGRAM_TOKEN 존재 여부: {'✅ 있음' if TOKEN else '❌ 없음'}")
print(f"CHAT_ID 존재 여부: {'✅ 있음' if CHAT_ID else '❌ 없음'}")

# 한국 시간 설정
now = datetime.datetime.now() + datetime.timedelta(hours=9)

async def main():
    if not all([SERVICE_KEY, TOKEN, CHAT_ID]):
        print("🚨 필수 설정값이 부족합니다. GitHub Secrets를 확인하세요.")
        return

    print(f"\n--- [Step 2] 기상청 API 호출 시도 ({now.strftime('%H:%M')}) ---")
    
    # 1. 기상청 API 테스트 (초단기실황)
    url = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    base_dt = now - datetime.timedelta(hours=1)
    params = {
        'serviceKey': SERVICE_KEY,
        'pageNo': '1', 'numOfRows': '10', 'dataType': 'JSON',
        'base_date': base_dt.strftime('%Y%m%d'),
        'base_time': base_dt.strftime('%H') + "00",
        'nx': 61, 'ny': 120
    }
    
    try:
        r = requests.get(url, params=params, timeout=10)
        print(f"API 응답 코드: {r.status_code}")
        data = r.json()
        result_code = data.get("response", {}).get("header", {}).get("resultCode")
        
        if result_code == "00":
            print("✅ 기상청 데이터 가져오기 성공!")
        else:
            print(f"❌ 기상청 API 에러 발생: {data.get('response', {}).get('header', {}).get('resultMsg')}")
            print(f"💡 가이드: API 키가 '승인' 상태인지, 혹은 일반 인증키(Decoding)를 넣었는지 확인하세요.")
    except Exception as e:
        print(f"❌ 기상청 연결 중 예외 발생: {e}")

    print("\n--- [Step 3] 텔레그램 전송 시도 ---")
    try:
        bot = Bot(token=TOKEN)
        # 봇 정보 확인 테스트
        bot_info = await bot.get_me()
        print(f"봇 연결 확인: @{bot_info.username}")
        
        test_msg = f"🔔 [디버깅] 테스트 메시지입니다.\n현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}"
        await bot.send_message(chat_id=CHAT_ID, text=test_msg)
        print("✅ 텔레그램 전송 성공!")
    except Exception as e:
        print(f"❌ 텔레그램 에러: {e}")
        print("💡 가이드: TOKEN이나 CHAT_ID가 정확한지 확인하세요. 봇을 먼저 채팅방에 초대했나요?")

if __name__ == "__main__":
    asyncio.run(main())
