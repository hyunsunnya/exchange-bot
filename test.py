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

# 실행 시간 제한 (07:00 ~ 07:30 사이만 실행)
if not (now.hour == 13 and 50 <= now.minute <= 30):
    print(f"현재 {now.strftime('%H:%M')} - 알림 시간이 아닙니다.")
    sys.exit()

def kma_get_json(url, params, timeout=15):
    """기상청 API 호출 공통 함수: 오류 상세 출력"""
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
    """초단기실황: 1시간 전 데이터를 요청하여 안전하게 기온 확보"""
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
    """단기예보: 오늘 전체 데이터를 훑어서 최저/최고기온을 확실히 확보"""
    url = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    
    # 최저기온(TMN)은 새벽 02:00 발표부터 포함되므로 base_time을 0200으로 고정
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
        # 해당 날짜의 예보 데이터만 필터링
        if item['fcstDate'] == target_str:
            category = item['category']
            value = item['fcstValue']
            
            # 최저/최고 기온 수집
            if category in ['TMN', 'TMX']:
                extracted[category] = value
            # 강수확률, 하늘상태 등은 아침 07:00 ~ 08:00 사이의 예보값 사용
            elif category in ['POP', 'SKY', 'PTY', 'TMP']:
                if '0700' <= item['fcstTime'] <= '0800':
                    extracted[category] = value
                    
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

    # 3. 메시지 포맷팅
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

    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown')
    print(f"✅ 전송 완료: {real_temp}도")

if __name__ == "__main__":
    asyncio.run(main())
