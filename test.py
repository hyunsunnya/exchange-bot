import requests
from bs4 import BeautifulSoup
import asyncio
import os
import datetime
import sys
from telegram import Bot

# GitHub Secrets 사용 (환경 변수)
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# [시간 설정] 한국 시간 기준 (UTC+9)
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# --- 실행 차단 조건 (테스트를 위해 주말/공휴일만 체크) ---

# 1. 주말 체크
if now.weekday() >= 5:
    print(f"오늘은 {now.strftime('%A')} (주말)입니다. 전송을 건너뜁니다.")
    sys.exit()

# 2. 2026년 한국 주요 공휴일 리스트
korea_holidays = [
    "2026-01-01", "2026-02-16", "2026-02-17", "2026-02-18",
    "2026-03-01", "2026-03-02", "2026-05-05", "2026-06-06",
    "2026-08-15", "2026-09-24", "2026-09-25", "2026-09-26",
    "2026-10-03", "2026-10-09", "2026-12-25"
]

today_str = now.strftime('%Y-%m-%d')
if today_str in korea_holidays:
    print(f"오늘은 공휴일({today_str})입니다. 전송을 건너뜁니다.")
    sys.exit()

# --- 💡 테스트를 위해 시간 제한(10:00~10:30) 로직은 삭제했습니다 ---

async def get_naver_exchange_rate(code):
    """
    네이버 금융에서 실시간 환율 데이터를 가져옵니다.
    """
    url = f"https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd={code}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 현재가 파싱
        current_price = float(soup.select_one(".value").text.replace(",", ""))
        
        # 전일비 및 등락률 파싱
        change_element = soup.select_one(".change").text.strip().split()
        change_amt = float(change_element[0].replace(",", ""))
        
        # 상승/하락 방향 체크
        direction = soup.select_one(".no_today .blind").text # '상승' 또는 '하락'
        if "하락" in direction:
            change_amt = -change_amt
            
        change_rate = float(soup.select_one(".point_status").text.strip().replace("%", ""))
        if "하락" in direction:
            change_rate = -change_rate

        return {
            'current': current_price,
            'change_amt': change_amt,
            'change_rate': change_rate
        }
    except Exception as e:
        print(f"Error fetching {code} from Naver: {e}")
        return None

async def main():
    if not TOKEN or not CHAT_ID: 
        print("❌ 설정 에러: TOKEN 또는 CHAT_ID가 없습니다.")
        return

    # 네이버 코드: FX_USDKRW (달러), FX_JPYKRW (엔화)
    usd = await get_naver_exchange_rate("FX_USDKRW")
    jpy = await get_naver_exchange_rate("FX_JPYKRW")
    
    msg_items = []
    
    if usd:
        mark = "🔺" if usd['change_rate'] > 0 else "🔻"
        if usd['change_rate'] == 0: mark = "━"
        msg_items.append(
            f"💵 **달러(USD/KRW)**\n"
            f"  • 현재가: `{usd['current']:,.2f}원`\n"
            f"  • 전일비: {mark} `{usd['change_amt']:+.2f}원` ({usd['change_rate']:+.2f}%)"
        )
    
    if jpy:
        mark = "🔺" if jpy['change_rate'] > 0 else "🔻"
        if jpy['change_rate'] == 0: mark = "━"
        msg_items.append(
            f"💴 **엔화(JPY/KRW 100)**\n"
            f"  • 현재가: `{jpy['current']:,.2f}원`\n"
            f"  • 전일비: {mark} `{jpy['change_amt']:+.2f}원` ({jpy['change_rate']:+.2f}%)"
        )
    
    if msg_items:
        final_msg = (
            f"📊 **데일리 환율 정보 (네이버 기준)**\n"
            f"📅 기준 시간: {now.strftime('%m/%d %H:%M')}\n"
            f"━━━━━━━━━━━━━━━\n\n"
            + "\n\n".join(msg_items)
        )
        
        try:
            bot = Bot(token=TOKEN)
            await bot.send_message(chat_id=CHAT_ID, text=final_msg, parse_mode='Markdown')
            print("✅ 텔레그램 전송 완료")
        except Exception as e:
            print(f"❌ 텔레그램 전송 실패: {e}")
    else:
        print("❌ 데이터를 가져오지 못했습니다.")

if __name__ == "__main__":
    asyncio.run(main())
