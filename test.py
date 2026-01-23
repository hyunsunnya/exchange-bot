import yfinance as yf
import asyncio
import os
import datetime
import sys
from telegram import Bot

# GitHub Secrets 사용
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# 한국 시간 기준 설정
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))

async def get_exchange_rate(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        data = ticker.history(period="5d", interval="1d") 
        
        if len(data) < 2:
            return None
            
        prev_close = data['Close'].iloc[-2]
        current_price = data['Close'].iloc[-1]
        
        price_change = current_price - prev_close
        change_rate = (price_change / prev_close) * 100
        
        return {
            'current': current_price, 
            'prev_close': prev_close,
            'change_amt': price_change,
            'change_rate': change_rate
        }
    except Exception as e:
        print(f"Error fetching {ticker_symbol}: {e}")
        return None

async def main():
    if not TOKEN or not CHAT_ID: 
        print("❌ 설정 에러: TOKEN 또는 CHAT_ID가 없습니다.")
        return

    usd = await get_exchange_rate("USDKRW=X")
    jpy = await get_exchange_rate("JPYKRW=X")
    
    msg_items = []
    
    # 달러 정보 구성
    if usd:
        mark = "🔺" if usd['change_rate'] > 0 else "🔻"
        msg_items.append(
            f"💵 **달러(USD/KRW)**\n"
            f"  • 현재가: `{usd['current']:,.2f}원`\n"
            f"  • 전일비: {mark} `{usd['change_amt']:+.2f}원` ({usd['change_rate']:+.2f}%)"
        )
    
    # 엔화 정보 구성 (100엔 기준)
    if jpy:
        curr_100 = jpy['current'] * 100
        amt_100 = jpy['change_amt'] * 100
        mark = "🔺" if jpy['change_rate'] > 0 else "🔻"
        msg_items.append(
            f"💴 **엔화(JPY/KRW 100)**\n"
            f"  • 현재가: `{curr_100:,.2f}원`\n"
            f"  • 전일비: {mark} `{amt_100:+.2f}원` ({jpy['change_rate']:+.2f}%)"
        )
    
    if msg_items:
        final_msg = (
            f"⚠️ **실시간 환율 변동 알림**\n"
            f"📅 기준 시간: {now.strftime('%m/%d %H:%M')}\n"
            f"━━━━━━━━━━━━━━━\n\n"
            + "\n\n".join(msg_items)
            + "\n\n━━━━━━━━━━━━━━━\n"
            f"오늘 하루도 화이팅입니다! 🚀"
        )
        
        try:
            bot = Bot(token=TOKEN)
            await bot.send_message(chat_id=CHAT_ID, text=final_msg, parse_mode='Markdown')
            print("✅ 상세 환율 알림 전송 완료")
        except Exception as e:
            print(f"❌ 텔레그램 전송 실패: {e}")
    else:
        print("❌ 데이터를 가져오는 데 실패했습니다.")

if __name__ == "__main__":
    asyncio.run(main())
