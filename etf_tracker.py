import requests
from bs4 import BeautifulSoup
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

def get_naver_price(code):
    """네이버 PC 금융 페이지에서 시세 추출 (더 안정적인 셀렉터 사용)"""
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    # 브라우저처럼 보이기 위한 헤더
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    
    res = requests.get(url, headers=headers, verify=False, timeout=20)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 1. 현재가 추출 (today 클래스 안의 em 탭)
    new_total = soup.select_one(".today .no_today")
    if not new_total:
        raise ValueError("현재가 데이터를 찾을 수 없습니다.")
    
    curr_price_text = new_total.select_one(".blind").text
    curr_price = int(curr_price_text.replace(",", ""))
    
    # 2. 전일비 추출
    diff_area = soup.select_one(".today .no_exday")
    if not diff_area:
        raise ValueError("전일비 데이터를 찾을 수 없습니다.")
        
    diff_text = diff_area.select_one(".blind").text.replace(",", "")
    diff_price = int(diff_text)
    
    # 3. 상승/하락 기호 확인 (ico_up/ico_down 혹은 '상승'/'하락' 텍스트)
    # n_red(상승), n_blue(하락) 클래스로 판단하는 것이 가장 정확합니다.
    if diff_area.select_one(".ico_up") or "상승" in str(diff_area):
        pass # diff_price 양수 유지
    elif diff_area.select_one(".ico_down") or "하락" in str(diff_area):
        diff_price = -diff_price
    else:
        diff_price = 0 # 보합
        
    prev_price = curr_price - diff_price
    # 전일 종가가 0이 될 수 없으므로 안전하게 계산
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
    lines = []
    lines.append(f"<b>📊 {datetime.now().strftime('%m월 %d일')} ETF 시세 리포트</b>")
    lines.append("━━━━━━━━━━━━━━━━━━")

    for name, code in ETF_TARGETS.items():
        try:
            curr_price, diff, pct = get_naver_price(code)
            
            mark = "🔺" if diff > 0 else "🔹" if diff < 0 else "⚪"
            line = f"<b>• {name}</b>\n  {curr_price:,.0f}원 ({mark} {abs(diff):,.0f}, {pct:+.2f}%)"
            lines.append(line)
            print(f"✅ {name} 데이터 수집 완료")
        except Exception as e:
            # 실패 시 로그를 남기고 리포트에도 표시
            print(f"❌ {name}({code}) 에러 발생: {e}")
            lines.append(f"<b>• {name}</b>\n  ❌ 데이터 로드 실패")

    return "\n\n".join(lines)

if __name__ == "__main__":
    print(f"🚀 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ETF 시세 수집 시작 (PC Crawling)...")
    report = get_etf_report()
    if report:
        send_telegram_message(report)
        print("✅ 리포트 전송 성공!")
