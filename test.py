import requests
import asyncio
import os
import datetime
import sys
from telegram import Bot

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

# 주말/공휴일 체크
if now.weekday() >= 5:
    sys.exit()

async def get_exchange_data():
    # 네이버 내부 API 주소 (가장 정확하고 빠름)
    url = "https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD,FRX.KRWJPY"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        results = {}
        for item in data:
            # USD, JPY 구분
            code = item['currencyCode']
            
            # 전일 대비 등락 정보 (RISE: 상승, FALL: 하락, EVEN: 보합)
            change_type = item['change']
            change_amt = item['changePrice']
            if change_type == "FALL":
                change_amt = -change_amt
                
            results[code] = {
                'current': item['basePrice'],
                'change_amt': change_amt,
                'change_rate': item['changeRate'] * 100 if change_type == "RISE" else -item['changeRate'] * 100 if change_type == "FALL" else 0.0
            }
        return results
    
    except Exception as e:
        print(f"❌ API 호출 에러: {e}")
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
    # 달러(USD) 정리
    if "USD" in data:
        usd = data["USD"]
        mark = "🔺" if usd['change_amt'] > 0 else "🔻" if usd['change_amt'] < 0 else "━"
        msg_items.append(
            f"💵 **미국 달러(USD)**\n"
            f"  • 현재가: `{usd['current']:,.2f}원`\n"
            f"  • 전일비: {mark} `{usd['change_amt']:+.2f}원` ({usd['change_rate']:+.2f}%)"
        )

    # 엔화(JPY) 정리
    if "JPY" in data:
        jpy = data["JPY"]
        # 네이버 API는 100엔 기준이므로 basePrice가 이미 100엔당 가격임
        mark = "🔺" if jpy['change_amt'] > 0 else "🔻" if jpy['change_amt'] < 0 else "━"
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
