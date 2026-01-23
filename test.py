import yfinance as yf
import asyncio
import os
import datetime
import sys
from telegram import Bot

# 환경 변수 로드
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

async def main():
    print("🚀 [Step 1] 텔레그램 설정 확인...")
    if not TOKEN or not CHAT_ID:
        print("❌ 설정 에러: TOKEN 또는 CHAT_ID가 없습니다.")
        return
    print(f"✅ 설정 확인 완료 (CHAT_ID: {CHAT_ID[:5]}***)")

    print("🚀 [Step 2] 환율 데이터 수집 시작 (yfinance)...")
    try:
        # 달러 환율 가져오기
        ticker = yf.Ticker("USDKRW=X")
        data = ticker.history(period="2d")
        
        if data.empty:
            print("❌ 환율 데이터를 가져오지 못했습니다.")
            return
            
        current_price = data['Close'].iloc[-1]
        print(f"✅ 현재 달러 환율: {current_price:.2f}원")

        # 메시지 전송
        bot = Bot(token=TOKEN)
        await bot.send_message(
            chat_id=CHAT_ID, 
            text=f"🔔 [테스트] 현재 달러 환율: {current_price:.2f}원",
            parse_mode='Markdown'
        )
        print("✅ 텔레그램 메시지 전송 성공!")

    except Exception as e:
        print(f"❌ 실행 중 에러 발생: {e}")

if __name__ == "__main__":
    asyncio.run(main())
