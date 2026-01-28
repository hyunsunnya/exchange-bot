import yfinance as yf
import asyncio
import os
import datetime
import sys
from telegram import Bot

# =========================
# 환경 변수
# =========================
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# =========================
# 한국 시간 (UTC+9)
# =========================
KST = datetime.timezone(datetime.timedelta(hours=9))
now = datetime.datetime.now(KST)

# =========================
# 1. 주말 체크
# =========================
if now.weekday() >= 5:
    print(f"오늘은 {now.strftime('%A')} (주말)입니다. 전송 스킵")
    sys.exit()

# =========================
# 2. 2026년 한국 공휴일
# =========================
korea_holidays = [
    "2026-01-01",
    "2026-02-16", "2026-02-17", "2026-02-18",
    "2026-03-01", "2026-03-02",
    "2026-05-05",
    "2026-06-06",
    "2026-08-15",
    "2026-09-24", "2026-09-25", "2026-09-26",
    "2026-10-03",
    "2026-10-09",
    "2026-12-25"
]

today_str = now.strftime('%Y-%m-%d')
if today_str in korea_holidays:
    print(f"오늘은 공휴일({today_str})입니다. 전송 스킵")
    sys.exit()

# =========================
# 3. 실행 시간 제한
# =========================
if not (now.hour == 10 and 0 <= now.minute <= 30):
    print(f"{now.strftime('%H:%M')} - 실행 시간이 아님")
    sys.exit()

# =========================
# 환율 조회 함수 (전일비 정확 버전)
# =========================
async def get_exchange_rate(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)

        # 최근 10일 → 마지막 2개 '확정 종가' 사용
        data = ticker.history(period="10d", interval="1d")
        data = data.dropna().sort_index()

        if len(data) < 2:
            return None

        prev_close = data['Close'].iloc[-2]
        current_close = data['Close'].iloc[-1]

        change_amt = current_close - prev_close
        change_rate = (change_amt / prev_close) * 100

        return {
            'current': float(current_close),
            'prev_close': float(prev_close),
            'change_amt': float(change_amt),
            'change_rate': float(change_rate)
        }

    except Exception as e:
        print(f"❌ {ticker_symbol} 조회 오류: {e}")
        return None

# =========================
# 메인 로직
# =========================
async def main():
    if not TOKEN or not CHAT_ID:
        print("❌ TOKEN 또는 CHAT_ID 없음")
        return

    usd = await get_exchange_rate("USDKRW=X")
    jpy = await get_exchange_rate("JPYKRW=X")

    msg_items = []

    if usd:
        mark = "🔺" if usd['change_rate'] > 0 else "🔻"
        msg_items.append(
            f"💵 *달러 (USD/KRW)*\n"
            f"  • 종가: `{usd['current']:,.2f}원`\n"
            f"  • 전일비: {mark} `{usd['change_amt']:+.2f}원` ({usd['change_rate']:+.2f}%)"
        )

    if jpy:
        curr_100 = jpy['current'] * 100
        amt_100 = jpy['change_amt'] * 100
        mark = "🔺" if jpy['change_rate'] > 0 else "🔻"
        msg_items.append(
            f"💴 *엔화 (JPY/KRW · 100엔)*\n"
            f"  • 종가: `{curr_100:,.2f}원`\n"
            f"  • 전일비: {mark} `{amt_100:+.2f}원` ({jpy['change_rate']:+.2f}%)"
        )

    if not msg_items:
        print("❌ 환율 데이터 없음")
        return

    final_msg = (
        f"📊 *데일리 환율 정보*\n"
        f"📅 기준일: {now.strftime('%m/%d')}\n"
        f"━━━━━━━━━━━━━━━\n\n"
        + "\n\n".join(msg_items)
    )

    try:
        bot = Bot(token=TOKEN)
        await bot.send_message(
            chat_id=CHAT_ID,
            text=final_msg,
            parse_mode="Markdown"
        )
        print("✅ 환율 알림 전송 완료")

    except Exception as e:
        print(f"❌ 텔레그램 전송 실패: {e}")

# =========================
# 실행
# =========================
if __name__ == "__main__":
    asyncio.run(main())
