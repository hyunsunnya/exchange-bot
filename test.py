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

# 지역 설정 (평일/주말 구분)
if now.weekday() < 5:
    REGION_NAME = "수원시 영통구"; NX, NY = 61, 120
else:
    REGION_NAME = "서울시 마포구"; NX, NY = 59, 127

def kma_get_json(url, params, timeout=15):
    try:
        r = requests.get(url, params=params, timeout=timeout)
        data = r.json()
        if data.get("response", {}).get("header", {}).get("resultCode") != "00":
            return None
        return data
    except:
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
                if category == 'TMP' and not ('0700' <= item['fcstTime'] <= '0900'): continue
                extracted[category] = item['fcstValue']
    return extracted

async def main():
    if not all([SERVICE_KEY, TOKEN, CHAT_ID]):
        print("❌ 환경변수 누락"); return

    real_temp = await get_realtime_temp()
    today_f = await get_forecast_data(now)
    yesterday_f = await get_forecast_data(yesterday)

    if real_temp is None or not today_f:
        print("❌ 데이터 수집 실패"); return

    # 1. 기온 비교 로직
    diff_msg = "어제랑 기온이 비슷해요 ⚖️"
    comment = "오늘 하루도 즐거운 하루 되세요! ✨"
    if yesterday_f and 'TMP' in yesterday_f:
        diff = real_temp - float(yesterday_f['TMP'])
        if diff > 0:
            diff_msg = f"어제보다 **{abs(diff):.1f}°** 높아요 📈"
            comment = "어제보다 포근한 아침이에요! 🌱"
        elif diff < 0:
            diff_msg = f"어제보다 **{abs(diff):.1f}°** 낮아요 📉"
            comment = "어제보다 더 쌀쌀하니 따뜻하게 입으세요! 🧣"

    # 2. 하늘 상태 로직
    sky_map = {'1': '반짝반짝 맑음 ☀️', '3': '구름많음 ☁️', '4': '흐림 ☁️'}
    sky_text = sky_map.get(today_f.get('SKY'), "정보없음")
    if today_f.get('PTY', '0') != '0': sky_text = "비/눈 소식 있음 ☔"

    # 3. 메시지 포맷팅 (원래 요청하신 스타일)
    msg = (f"🌈 **똑똑! 오늘의 날씨 배달왔어요!**\n"
           f"📍 `{REGION_NAME}` 기준 ({now.strftime('%m월 %d일')})\n"
           f"━━━━━━━━━━━━━━━\n\n"
           f"🌡️ **지금 기온:** `{real_temp}°C`\n"
           f"💬 {diff_msg}\n"
           f"💡 {comment}\n\n"
           f"✨ **하늘 상태:** {sky_text}\n"
           f"☔ **강수 확률:** {today_f.get('POP', '0')}% 입니당!\n"
           f"📉 **최저/최고:** `{today_f.get('TMN', '-')}°` / `{today_f.get('TMX', '-')}°` \n\n"
           f"━━━━━━━━━━━━━━━\n"
           f"오늘 하루도 기분 좋게 시작하기! 파이팅이에요! ٩(◕ᗜ◕)و💖")

    try:
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
        print(f"✅ 알림 전송 완료")
    except Exception as e:
        print(f"❌ 전송 에러: {e}")

if __name__ == "__main__":
    asyncio.run(main())
