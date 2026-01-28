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

# 주말/공휴일 체크 (테스트 완료 후 필요시 활성화)
if now.weekday() >= 5:
    sys.exit()

async def get_exchange_data():
    # 상세 페이지 대신 시장지수 메인 페이지 사용 (더 안정적임)
    url = "https://finance.naver.com/marketindex/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content.decode('euc-kr', 'replace'), 'html.parser')
        
        results = {}
        # 주요 통화 리스트 추출
        exchange_list = soup.select(".exchange_list > li")
        
        for item in exchange_list:
            title = item.select_one(".h_lst").text.strip()
            # 달러와 엔화만 골라내기
            if "미국 USD" in title or "일본 JPY" in title:
                key = "USD" if "미국" in title else "JPY"
                value = float(item.select_one(".value").text.replace(",", ""))
                change = float(item.select_one(".change").text.replace(",", ""))
                
                # 상승/하락 판정
                blind_text = item.select_one(".blind").text
                if "하락" in blind_text:
                    change = -change
                
                # 등락률 계산 (메인 페이지엔 비율이 없으므로 직접 계산)
                # 전일가 = 현재가 - 변동분
                prev_val = value - change
                rate = (change / prev_val) * 100
                
                results[key] = {
                    'current': value,
                    'change_amt': change,
                    'change_rate': rate
                }
        return results
    
    except Exception as e:
        print(f"❌ 데이터 수집 중 에러 발생: {e}")
        return None

async def main():
    if not TOKEN or not CHAT_ID: 
        print("❌ 설정 에러: TOKEN 또는 CHAT_ID가 없습니다.")
        return

    print(f"🚀 {now.strftime('%Y-%m-%d %H:%M:%S')} 데이터 수집 시작...")
    data = await get_exchange_data()
    
    if not data:
        print("❌ 데이터를 가져오지 못했습니다.")
        return

    msg_items = []
    # 달러 정보 정리
    if "USD" in data:
        usd = data["USD"]
        mark = "🔺" if usd['change_rate'] > 0 else "🔻"
        if usd['change_rate'] == 0: mark = "━"
        msg_items.append(
            f"💵 **미국 달러(USD)**\n"
            f"  • 현재가: `{usd['current']:,.2f}원`\n"
            f"  • 전일비: {mark} `{usd['change_amt']:+.2f}원` ({usd['change_rate']:+.2f}%)"
        )

    # 엔화 정보 정리
    if "JPY" in data:
        jpy = data["JPY"]
        mark = "🔺" if jpy['change_rate'] > 0 else "🔻"
        if jpy['change_rate'] == 0: mark = "━"
        msg_items.append(
            f"💴 **일본 엔화(JPY/100)**\n"
            f"  • 현재가: `{jpy['current']:,.2f}원`\n"
            f"  • 전일비: {mark} `{jpy['change_amt']:+.2f}원` ({jpy['change_rate']:+.2f}%)"
        )
    
    if msg_items:
        final_msg = (
            f"📊 **데일리 환율 정보 (네이버)**\n"
            f"📅 기준 시간: {now.strftime('%m/%d %H:%M')}\n"
            f"━━━━━━━━━━━━━━━\n\n"
            + "\n\n".join(msg_items)
        )
        
        try:
            bot = Bot(token=TOKEN)
            await bot.send_message(chat_id=CHAT_ID, text=final_msg, parse_mode='Markdown')
            print("✅ 텔레그램 전송 성공!")
        except Exception as e:
            print(f"❌ 텔레그램 전송 실패: {e}")

if __name__ == "__main__":
    asyncio.run(main())
