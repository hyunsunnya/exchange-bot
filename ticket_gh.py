import requests
from bs4 import BeautifulSoup
import os
import warnings

warnings.filterwarnings("ignore")

TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.json()
    except Exception as e:
        print(f"❌ 전송 에러: {e}")
        return None

def get_combined_news():
    """구글 뉴스를 활용해 일반 뉴스 + NOL티켓 내부 소식을 모두 수집"""
    # 쿼리 설명: 
    # 1. (티켓 오픈 콘서트 뮤지컬) -> 일반 뉴스 검색
    # 2. site:nolticket.com -> NOL티켓 사이트 내부의 신규 페이지 검색
    queries = [
        "티켓 오픈 콘서트 뮤지컬 페스티벌",
        "site:nolticket.com" 
    ]
    
    all_events = []
    seen_titles = []

    headers = {'User-Agent': 'Mozilla/5.0'}

    for q in queries:
        url = f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.find_all('item')

            print(f"🔍 쿼리 [{q}] 검색 중... {len(items)}건 발견")

            count = 0
            for item in items:
                title = item.title.text if item.title else ""
                link = item.find('link').next_element.strip() if item.find('link') else ""
                
                # 중복 방지 로직
                clean_title = title.split(' - ')[0]
                short_title = clean_title[:10].replace(" ", "")
                
                if not any(short_title in seen or seen in short_title for seen in seen_titles):
                    # 출처 표시
                    prefix = "🎫 [NOL티켓]" if "nolticket.com" in link else "📰 [뉴스]"
                    all_events.append(f"{prefix} **{clean_title}**\n🔗 [자세히 보기]({link})")
                    seen_titles.append(short_title)
                    count += 1
                
                if count >= 5: break # 각 쿼리당 최대 5개
        except Exception as e:
            print(f"❌ 검색 에러 [{q}]: {e}")

    return all_events

if __name__ == "__main__":
    if not TOKEN or not CHAT_ID:
        print("❌ 설정 에러: GitHub Secrets를 확인하세요.")
    else:
        print("🚀 통합 소식 수집 시작...")
        results = get_combined_news()
        
        if results:
            msg = "📅 **오늘의 통합 티켓 소식**\n"
            msg += "━━━━━━━━━━━━━━━\n\n"
            msg += "\n\n".join(results)
            
            send_telegram_message(msg)
            print(f"✅ 총 {len(results)}건 전송 완료!")
        else:
            print("✅ 새로운 소식이 없습니다.")
