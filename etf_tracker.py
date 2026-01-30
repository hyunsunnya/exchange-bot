import requests
from bs4 import BeautifulSoup
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = "7874043423:AAEtpCMnZpG9lOzMHfwd1LxumLiAB-_oNAw"
CHAT_ID = "-1003615231060"

# 대상 ETF 목록
ETF_TARGETS = {
    "TIGER KRX금현물": "481470",
    "KODEX 200": "069500",
    "TIGER 미국나스닥100": "133690",
    "KODEX 코스닥150": "229200",
    "TIGER 미국S&P500": "360750"
}

def get_naver_price(code, name):
    """네이버 금융 및 검색 결과를 활용한 시세 추출"""
    # 1차 시도: 네이버 금융 일반 페이지
    url = f"https://finance.naver.com/item/main.naver?code={code}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 가격 데이터 추출 시도
        price_area = soup.select_one(".today")
        if not price_area or not price_area.select_one(".blind"):
            # 2차 시도: 네이버 검색 시세 페이지 (금현물 같은 특수 종목용)
            search_url = f"https://search.naver.com/search.naver?query={code}"
            res = requests.get(search_url, headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 검색 결과 내 시세 영역 추출 (지식베이스/주식정보)
            curr_price = int(soup.select_one(".spt_con strong").text.replace(",", ""))
            diff_text = soup.select_one(".spt_con .n_ch").text.replace(",", "").replace("상승", "").replace("하락", "").strip()
            diff_price = int(diff_text.split(" ")[0])
            
            # 등락 판별
            if "down" in str(soup.select_one(".spt_con .n_ch")) or "하락" in str(soup.select_one(".spt_con .n_ch")):
                diff_price = -diff_price
        else:
            # 일반적인 네이버 금융 구조
            curr_price = int(price_area.select_one(".no_today .blind").text.replace(",", ""))
            diff_area = price_area.select_one(".no_exday")
            diff_price = int(diff_area.select_one(".blind").text.replace(",", ""))
            if "down" in str(diff_area) or "하락" in str(diff_area):
                diff_price = -diff_price
                
        prev_price = curr_price - diff_price
        pct = (diff_price / prev_price * 100) if prev_price != 0 else 0
        return curr_price, diff_price, pct

    except Exception as e:
        print(f"❌ {name} 추출 중 상세 에러: {e}")
        raise e

def get_etf_report():
    lines = [f"<b>📊 {datetime.now().strftime('%m월 %d일')} ETF 시세 리포트</b>", "━━━━━━━━━━━━━━━━━━"]

    for name, code in ETF_TARGETS.items():
        try:
            curr, diff, pct = get_naver_price(code, name)
            mark = "🔺" if diff > 0 else "🔹" if diff < 0 else "⚪"
            lines.append(f"<b>• {name}</b>\n  {curr:,.0f}원 ({mark} {abs(diff):,.0f}, {pct:+.2f}%)")
            print(f"✅ {name} 완료")
        except:
            lines.append(f"<b>• {name}</b>\n  ❌ 데이터 로드 실패")

    return "\n\n".join(lines)

if __name__ == "__main__":
    report = get_etf_report()
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  json={"chat_id": CHAT_ID, "text": report, "parse_mode": "HTML"})
