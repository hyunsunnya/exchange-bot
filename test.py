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
yesterday = now - datetime.timedelta(days=1)

# 지역 설정
if now.weekday() < 5:
    REGION_NAME = "수원시 영통구"; NX, NY = 61, 120
else:
    REGION_NAME = "서울시 마포구"; NX, NY = 59, 127

# [수정] 테스트를 위해 실행 시간 제한 로직을 제거했습니다.
print(f"🚀 테스트 실행 중... (현재 한국 시간: {now.strftime('%H:%M')})")

def kma_get_json(url, params, timeout=15):
    try:
        r = requests.get(url, params=params, timeout=timeout)
        data = r.json()
        header = data.get("response", {}).get("header", {})
        if header.get("resultCode") != "00":
            print(f"❌ KMA 에러: {header.get('resultMsg')} ({header.get('resultCode')})")
            return None
        return data
    except Exception as e:
        print(f"❌ 호출 실패: {e}")
        return None

async def get_realtime_temp():
    url = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    base_dt = now - datetime.timedelta(hours=1)
    params = {
        'serviceKey': SERVICE_KEY, 'pageNo': '1', 'numOfRows': '100', 'dataType': 'JSON',
        'base_date': base_dt.strftime('%Y%m%d'),
        'base_time': base_dt.strftime('%H') + "00",
        'nx': NX, 'ny': NY
    }
    data = kma_get_json(url, params)
    if not data: return None
    items = data['response']['body']['items']['item']
    for item in items:
        if item['category'] == 'T1H': return float(item['obsrValue'])
    return None

async def get_forecast_data(target_date):
    url = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    params = {
        'serviceKey': SERVICE_KEY, 'pageNo': '1', 'numOfRows': '1000', 'dataType': 'JSON',
        'base_date': target_date.strftime('%Y%m%d'),
        'base_time': '0200', 
        'nx': NX, 'ny': NY
    }
    data = kma_get_json(url, params)
    if not data: return None
    items = data['response']['body']['items']['item']
    extracted = {}
    target_str = target_date.strftime('%Y%m%d')
    for item in items:
        if item['fcstDate'] == target_str:
            category = item['category']
            if category in ['TMN', 'TMX', 'POP', 'SKY', 'PTY', 'TMP']:
                extracted[category] = item['fcstValue']
    return extracted

async def main():
    if not all([SERVICE_KEY, TOKEN, CHAT_ID]):
        print(f"❌ 환경변수 확인 필요: KMA_API_KEY={bool(SERVICE_KEY)}, TOKEN={bool(TOKEN)}, CHAT_ID={bool(CHAT_ID)}")
        return

    real_temp = await get_realtime_temp()
    today_f = await get_forecast_data(now)
    yesterday_f = await get_forecast_data(yesterday)

    if real_temp is None:
        print("❌ 실시간 기온 데이터 수집 실패 (기상청 점검 시간일 수 있습니다)"); return

    # 메시지 생성 로직 (기존과 동일)
    diff_msg = "어제랑 기온이 비슷해요 ⚖️"
    if yesterday_f and 'TMP' in yesterday_f:
        diff = real_temp - float(yesterday_f['TMP'])
        if diff > 0: diff_msg = f"어제보다 **{abs(diff):.1f}°** 높아요 📈"
        elif diff < 0: diff_msg = f"어제보다 **{abs(diff):.1f}°** 낮아요 📉"

    msg = (f"🌈 **[테스트] 오늘의 날씨 알림**\n"
           f"📍 `{REGION_NAME}` ({now.strftime('%m월 %d일')})\n"
           f"🌡️ **현재:** `{real_temp}°C` | {diff_msg}\n"
           f"📉 **최저/최고:** `{today_f.get('TMN', '-')}°` / `{today_f.get('TMX', '-')}°` \n")

    try:
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
        print(f"✅ 전송 성공: {real_temp}도")
    except Exception as e:
        print(f"❌ 텔레그램 전송 실패: {e}")

if __name__ == "__main__":
    asyncio.run(main())
