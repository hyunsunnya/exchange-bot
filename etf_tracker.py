import yfinance as yf
import requests
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = "7874043423:AAEtpCMnZpG9lOzMHfwd1LxumLiAB-_oNAw"
CHAT_ID = "-1003615231060"

ETF_TARGETS = {
    "TIGER KRX금현물": "408060.KS",
    "KODEX 200": "069500.KS",
    "TIGER 미국나스닥100": "133690.KS",
    "KODEX 코스닥150": "229200.KS",
    "TIGER 미국S&P500": "360750.KS"
}

def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        # verify=False와 함께 timeout을 넉넉히 잡습니다.
        res = requests.post(url, json=payload, timeout=30, verify=False)
        print(f"📡 텔레그램 응답 상태: {res.status_code}") # 상태 코드 출력 로그 추가
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"❌ 전송 실패 상세: {e}")
    return None

def get_etf_report():
    lines = []
    lines.append(f"<b>📊 {datetime.now().strftime('%m월 %d일')} ETF 시세 리포트</b>")
    lines.append("━━━━━━━━━━━━━━━━━━")

    for name, ticker in ETF_TARGETS.items():
        try:
            # 기간을 7일로 넉넉히 잡고 마지막 2개의 행(row)을 분석
            stock = yf.Ticker(ticker)
            df = stock.history(period="7d")
            
            if df.empty or len(df) < 2:
                print(f"⚠️ {name}({ticker}) 데이터를 가져오지 못했습니다.")
                continue

            # 가장 마지막 데이터와 그 이전 데이터 추출
            curr_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[-2]
            
            change = curr_price - prev_price
            change_pct = (change / prev_price) * 100
            
            mark = "🔺" if change > 0 else "🔹" if change < 0 else "⚪"
            
            line = f"<b>• {name}</b>\n  {curr_price:,.0f}원 ({mark} {change:+,.0f}, {change_pct:+.2f}%)"
            lines.append(line)
            print(f"✅ {name} 데이터 수집 완료")
        except Exception as e:
            print(f"❌ {name} 처리 중 에러: {e}")

    if len(lines) <= 2: # 헤더만 있고 데이터가 없는 경우
        return None
        
    return "\n\n".join(lines)

if __name__ == "__main__":
    print(f"🚀 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ETF 시세 수집 시작...")
    report = get_etf_report()
    
    if report:
        print("📝 리포트 생성 완료. 텔레그램 전송 시도...")
        success = send_telegram_message(report)
        if success:
            print("✅ 텔레그램 전송 성공!")
    else:
        print("⚠️ 전송할 데이터가 없습니다.")
