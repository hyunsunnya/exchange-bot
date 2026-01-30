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
    """네이버 시세 API를 직접 호출하여 데이터 획득 (가장 확실한 방법)"""
    # 네이버에서 실시간 시세를 가져오는 API 주소
    url = f"https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{code}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    res = requests.get(url, headers=headers, verify=False, timeout=15)
    res_data = res.json()
    
    # API 응답에서 필요한 데이터 추출
    item = res_data['result']['areas'][0]['datas'][0]
    
    curr_price = int(item['nv'].replace(",", ""))  # 현재가 (now value)
    diff_price = int(item['cv'].replace(",", ""))  # 전일비 (compare value)
    
    # 등락 구분 (2: 상승, 5: 하락, 3: 보합)
    rf = item['rf']
    if rf == "5":
        diff_price = -diff_price
    elif rf == "3":
        diff_price = 0
        
    prev_price = curr_price - diff_price
    change_pct = (diff_price / prev_price * 100) if prev_price != 0 else 0
    
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
    lines = [f"<b>📊 {datetime.now().strftime('%m월 %d일')} ETF 시세 리포트</b>", "━━━━━━━━━━━━━━━━━━"]

    for name, code in ETF_TARGETS.items():
        try:
            curr, diff, pct = get_etf_data(code)
            mark = "🔺" if diff > 0 else "🔹" if diff < 0 else "⚪"
            # 절대값 abs(diff)를 사용하여 기호와 숫자가 겹치지 않게 처리
            lines.append(f"<b>• {name}</b>\n  {curr:,.0f}원 ({mark} {abs(diff):,.0f}, {pct:+.2f}%)")
            print(f"✅ {name} 완료")
        except Exception as e:
            print(f"❌ {name}({code}) 에러: {e}")
            lines.append(f"<b>• {name}</b>\n  ❌ 데이터 로드 실패")

    return "\n\n".join(lines)

if __name__ == "__main__":
    print(f"🚀 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ETF 시세 수집 시작 (API)...")
    report = get_etf_report()
    if report:
        send_telegram_message(report)
        print("✅ 리포트 전송 성공!")
