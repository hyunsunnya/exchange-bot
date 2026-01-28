import requests
from bs4 import BeautifulSoup
import asyncio
import os
import datetime
import sys
from telegram import Bot

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# 주말/공휴일 체크 (테스트 시 필요하면 유지)
if now.weekday() >= 5:
    sys.exit()

async def get_naver_exchange_rate(code):
    # 상세 페이지보다 데이터 추출이 쉬운 메인 인덱스 URL 사용 고려
    url = f"https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd={code}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 데이터 추출 시도 (에러 방지를 위해 find 사용)
        value_tag = soup.find("em", {"class": "cur_value"}) or soup.select_one(".value")
        if not value_tag:
            print(f"❌ {code}: 가격 태그를 찾을 수 없습니다.")
            return None
            
        current_price = float(value_tag.text.replace(",", ""))
        
        # 전일비 및 등락률 파싱
        change_tag = soup.select_one(".change")
        if not change_tag:
            print(f"❌ {code}: 등락 태그를 찾을 수 없습니다.")
            return None
            
        change_amt = float(change_tag.text.strip().split()[0].replace(",", ""))
        
        # 등락 방향 (상승/하락) 확인
        # 네이버는 부모 요소의 클래스명(up/down)이나 blind 텍스트로 구분
        no_today = soup.select_one(".no_today")
        direction = no_today.text if no_today else ""
        
        if "하락" in direction:
            change_amt = -change_amt
            
        point_tag = soup.select_one(".point_status")
        change_rate = float(point_tag.text.strip().replace("%", "")) if point_tag else 0.0
        if "하락" in direction:
            change_rate = -change_rate

        return {'current': current_price, 'change_amt': change_amt, 'change_rate': change_rate}
    
    except Exception as e:
        print(f"❌ {code} 파싱 에러: {e}")
        return None

async def main():
    if not TOKEN or not CHAT_ID: return

    usd = await get_naver_exchange_rate("FX_USDKRW")
    jpy = await get_naver_exchange_rate("FX_JPYKRW")
    
    msg_items = []
    for data, name in [(usd, "💵 달러(USD)"), (jpy, "💴 엔화(JPY/100)")]:
        if data:
            mark = "🔺" if data['change_rate'] > 0 else "🔻"
            if data['change_rate'] == 0: mark = "━"
            msg_items.append(
                f"{name}\n"
                f"  • 현재가: `{data['current']:,.2f}원`\n"
                f"  • 전일비: {mark} `{data['change_amt']:+.2f}원` ({data['change_rate']:+.2f}%)"
            )
    
    if msg_items:
        final_msg = f"📊 **데일리 환율 정보 (Naver)**\n📅 {now.strftime('%m/%d %H:%M')}\n\n" + "\n\n".join(msg_items)
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=final_msg, parse_mode='Markdown')
        print("✅ 전송 성공!")
    else:
        print("❌ 전송할 데이터가 없습니다.")

if __name__ == "__main__":
    asyncio.run(main())
