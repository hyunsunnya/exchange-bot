import requests
import warnings
from datetime import datetime

# SSL 경고 무시
warnings.filterwarnings("ignore")
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = "7874043423:AAEtpCMnZpG9lOzMHfwd1LxumLiAB-_oNAw"
CHAT_ID = "-1003615231060"

# 대상 ETF 목록 (종목코드)
ETF_TARGETS = {
    "TIGER KRX금현물": "481470",
    "KODEX 200": "069500",
    "TIGER 미국나스닥100": "133690",
    "KODEX 코스닥150": "229200",
    "TIGER 미국S&P500": "360750"
}

def get_etf_data(code):
    """네이버 모바일 API를 사용하여 실시간 시세 데이터 획득"""
    # 네이버 주식 모바일 API URL
    url = f"https://m.stock.naver.com/api/stock/{code}/basic"
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
    }
    
    response = requests.get(url, headers=headers, verify=False, timeout=15)
    data = response.json()
    
    # 필요한 정보 추출
    curr_price = int(data['closePrice'].replace(",", "")) # 현재가
    diff_price = int(data['compareToPreviousClosePrice'].replace(",", "")) # 전일비
    # 등락 기호 확인 (상승/하락/보합)
    fluctuation = data['fluctuationCode'] 
    
    if fluctuation == "5": # 하락인 경우 마이너스 처리
        diff_price = -diff_price
    elif fluctuation == "3": # 보합인 경우
        diff_price = 0
        
    prev_price = curr_price - diff_price
    change_pct = (diff_price / prev_price) * 100
    
    return curr_price, diff_price, change_pct

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

    for name, code in ETF_TARGETS.items():
        try:
            curr_price, diff, pct = get_etf_data(code)
            
            mark = "🔺" if diff > 0 else "🔹" if diff < 0 else "⚪"
            line = f"<b>• {name}</b>\n  {curr_price:,.0f}원 ({mark} {diff:+,.0f}, {pct:+.2f}%)"
            lines.append(line)
            print(f"✅ {name} 데이터 수집 완료")
        except Exception as e:
            print(f"❌ {name}({code}) 에러: {e}")
            lines.append(f"<b>• {name}</b>\n  데이터 로드 실패")

    return "\n\n".join(lines)

if __name__ == "__main__":
    print(f"🚀 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ETF 시세 수집 시작 (Mobile API)...")
    report = get_etf_report()
    if report:
        send_telegram_message(report)
        print("✅ 리포트 전송 성공!")
