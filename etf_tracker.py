import requests
from bs4 import BeautifulSoup
import warnings
import json
import re
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

def get_naver_etf_price(code):
    """네이버 금융 페이지 내 임베딩된 JSON 데이터를 직접 파싱"""
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    res = requests.get(url, headers=headers, verify=False, timeout=20)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 1. HTML 태그 방식 (우선 시도)
    try:
        price_area = soup.select_one(".today")
        if price_area:
            curr_price = int(price_area.select_one(".no_today .blind").text.replace(",", ""))
            diff_area = price_area.select_one(".no_exday")
            diff_price = int(diff_area.select_one(".blind").text.replace(",", ""))
            
            # 상승/하락 여부 판단
            if "ico_down" in str(diff_area) or "하락" in str(diff_area):
                diff_price = -diff_price
            
            prev_price = curr_price - diff_price
            pct = (diff_price / prev_price * 100) if prev_price != 0 else 0
            return curr_price, diff_price, pct
    except:
        pass

    # 2. 스크립트 정규식 방식 (태그 방식 실패 시 대안)
    # 네이버 금융 페이지 내 'now_value' 등의 키워드가 포함된 스크립트 영역을 찾습니다.
    try:
        script_data = re.search(r"var\s+itemCurrentPrice\s+=\s+(\{.*?\});", res.text, re.S)
        if not script_data:
            # 다른 패턴 시도
            curr_price = int(re.search(r'now_value">([\d,]+)', res.text).group(1).replace(",", ""))
            diff_price = int(re.search(r'area_delta">.*?blind">([\d,]+)', res.text, re.S).group(1).replace(",", ""))
            if "🔻" in res.text or "하락" in res.text:
                diff_price = -diff_price
            prev_price = curr_price - diff_price
            pct = (diff_price / prev_price * 100)
            return curr_price, diff_price, pct
    except Exception as e:
        raise ValueError(f"데이터 추출 실패: {e}")

def get_etf_report():
    lines = [f"<b>📊 {datetime.now().strftime('%m월 %d일')} ETF 시세 리포트</b>", "━━━━━━━━━━━━━━━━━━"]

    for name, code in ETF_TARGETS.items():
        try:
            curr, diff, pct = get_naver_etf_price(code)
            mark = "🔺" if diff > 0 else "🔹" if diff < 0 else "⚪"
            lines.append(f"<b>• {name}</b>\n  {curr:,.0f}원 ({mark} {abs(diff):,.0f}, {pct:+.2f}%)")
            print(f"✅ {name} 완료")
        except Exception as e:
            print(f"❌ {name}({code}) 에러: {e}")
            lines.append(f"<b>• {name}</b>\n  ❌ 데이터 로드 실패")

    return "\n\n".join(lines)

if __name__ == "__main__":
    print(f"🚀 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ETF 시세 수집 시작...")
    report = get_etf_report()
    
    # 텔레그램 전송
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": report, "parse_mode": "HTML"}
    res = requests.post(url, json=payload, timeout=30, verify=False)
    
    if res.status_code == 200:
        print("✅ 리포트 전송 성공!")
    else:
        print(f"❌ 전송 실패: {res.text}")
