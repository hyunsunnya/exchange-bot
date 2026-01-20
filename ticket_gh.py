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
    """구글 뉴스 RSS를 이용해 일반 뉴스 + 놀 인터파크 최신 페이지 수집"""
    # 쿼리: 일반 티켓 뉴스 + 놀 인터파크 사이트 내부 검색
    queries = [
        "티켓 오픈 콘서트 뮤지컬 페스티벌",
        "site:nol.interpark.com" 
    ]
    
    all_events = []
    seen_titles = []
    headers = {'User-Agent': 'Mozilla/5.0'}

    for q in queries:
        # 구글 뉴스 RSS를 통해 해당 사이트의 최신 색인 정보를 가져옴
        url = f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.find_all('item')

            print(f"🔍 쿼리 [{q}] 검색 중...")

            count = 0
            for item in items:
                title = item.title.text if item.title else ""
                link = item.find('link').next_element.strip() if item.find('link') else ""
                
                # 중복 제거 로직
                clean_title = title.split(' - ')[0]
                short_title = clean_title[:10].replace(" ", "")
                
                if not any(short_title in seen or seen in short_title for seen in seen_titles):
                    # 출처 태그 달기
                    if "nol.interpark.com" in link:
                        prefix = "🎫 [놀 인터파크]"
                    else:
                        prefix = "📰 [뉴스]"
                        
                    all_events.append(f"{prefix} **{clean_title}**\n🔗 [자세히 보기]({link})")
                    seen_titles.append(short_title)
                    count += 1
                
                if count >= 5: break # 각 항목당 5개씩
        except Exception as e:
            print(f"❌ 검색 에러 [{q}]: {e}")

    return all_events

if __name__ == "__main__":
    if not TOKEN or not CHAT_ID:
        print("❌ 설정 에러: GitHub Secrets를 확인하세요.")
    else:
        print(f"🚀 놀 인터파크 통합 수집 시작... (ID: {CHAT_ID})")
        results = get_combined_news()
        
        if results:
            msg = "📅 **오늘의 놀 티켓 & 공연 소식**\n"
            msg += "━━━━━━━━━━━━━━━\n\n"
            msg += "\n\n".join(results)
            
            send_telegram_message(msg)
            print(f"✅ 총 {len(results)}건 전송 완료!")
        else:
            print("✅ 새로운 소식이 없습니다.")
