import yfinance as yf
import requests
import time
import warnings
from datetime import datetime

# SSL 경고 무시
warnings.filterwarnings("ignore")
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# [설정] 기존에 사용하시던 값과 동일하게 세팅
TOKEN = "7874043423:AAEtpCMnZpG9lOzMHfwd1LxumLiAB-_oNAw"
CHAT_ID = "-1003615231060"

# 대상 ETF 목록 (종목명: 티커)
ETF_TARGETS = {
    "TIGER KRX금현물": "408060.KS",
    "KODEX 200": "069500.KS",
    "TIGER 미국나스닥100": "133690.KS",
    "KODEX 코스닥150": "229200.KS",
    "TIGER 미국S&P500": "360750.KS"
}

def send_telegram_message(text: str):
    """텔레그램 메시지 전송"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        res = requests.post(url, json=payload, timeout=20, verify=False)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"❌ 전송 실패: {e}")
    return None

def get_etf_report():
    """ETF 시세 데이터 수집 및 HTML 리포트 생성"""
    lines = []
    lines.append(f"<b>📊 {datetime.now().strftime('%m월 %d일')} ETF 시세 리포트</b>")
    lines.append("━━━━━━━━━━━━━━━━━━")

    for name, ticker in ETF_TARGETS.items():
        try:
            # 전일 종가와 현재가를 가져오기 위해 5일치 데이터 수집
            stock = yf.Ticker(ticker)
            df = stock.history(period="5d")
            
            if len(df) < 2:
                continue

            curr_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[-2]
            change = curr_price - prev_price
            change_pct = (change / prev_price) * 100
            
            # 등락 기호 설정
            mark = "🔺" if change > 0 else "🔹" if change < 0 else "⚪"
            
            line = f"<b>• {name}</b>\n  {curr_price:,.0f}원 ({mark} {change:+,.0f}, {change_pct:+.2f}%)"
            lines.append(line)
        except Exception as e:
            lines.append(f"• {name}: 데이터 로드 실패")
            print(f"Error fetching {name}: {e}")

    return "\n\n".join(lines)

if __name__ == "__main__":
    print(f"🚀 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ETF 시세 수집 시작...")
    report = get_etf_report()
    
    if report:
        success = send_telegram_message(report)
        if success:
            print("✅ ETF 시세 전송 완료!")
