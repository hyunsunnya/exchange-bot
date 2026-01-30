import yfinance as yf
import requests
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = "7874043423:AAEtpCMnZpG9lOzMHfwd1LxumLiAB-_oNAw"
CHAT_ID = "-1003615231060"

# Yahoo Finance에서 데이터가 잘 잡히는 티커로 재수정
ETF_TARGETS = {
    "TIGER KRX금현물": "408060.KS", 
    "KODEX 200": "069500.KS",
    "TIGER 미국나스닥100": "133690.KS",
    "KODEX 코스닥150": "229200.KS",
    "TIGER 미국S&P500": "360750.KS"
}

def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        res = requests.post(url, json=payload, timeout=30, verify=False)
        return res.json()
    except Exception as e:
        print(f"❌ 전송 실패: {e}")
    return None

def get_etf_report():
    lines = []
    lines.append(f"<b>📊 {datetime.now().strftime('%m월 %d일')} ETF 시세 리포트</b>")
    lines.append("━━━━━━━━━━━━━━━━━━")

    for name, ticker in ETF_TARGETS.items():
        try:
            stock = yf.Ticker(ticker)
            # 데이터를 좀 더 넉넉하게(1mo) 가져와서 최신 영업일 2개를 추출합니다.
            df = stock.history(period="1mo")
            
            if df.empty or len(df) < 2:
                print(f"⚠️ {name}({ticker}) 데이터를 찾을 수 없어 건너뜁니다.")
                continue

            curr_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[-2]
            change = curr_price - prev_price
            change_pct = (change / prev_price) * 100
            
            mark = "🔺" if change > 0 else "🔹" if change < 0 else "⚪"
            line = f"<b>• {name}</b>\n  {curr_price:,.0f}원 ({mark} {change:+,.0f}, {change_pct:+.2f}%)"
            lines.append(line)
            print(f"✅ {name} 데이터 수집 완료")
            
        except Exception as e:
            print(f"❌ {name}({ticker}) 처리 중 에러: {e}")

    if len(lines) <= 2:
        return None
    return "\n\n".join(lines)

if __name__ == "__main__":
    print(f"🚀 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ETF 시세 수집 시작...")
    report = get_etf_report()
    if report:
        send_telegram_message(report)
        print("✅ 리포트 전송 성공!")
    else:
        print("⚠️ 전송할 데이터가 없습니다.")
