import requests
from bs4 import BeautifulSoup
import os

# --- GitHub Secrets에서 설정값 불러오기 ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

KEYWORDS = ["콘서트", "페스티벌", "내한", "전시", "오픈", "티켓", "공연"]

def send_telegram_message(text):
    """텔레그램 메시지 전송 함수"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        res_data = res.json()
        if not res_data.get("ok"):
            print(f"❌ 텔레그램 에러: {res_data.get('description')}")
        return res_data
    except Exception as e:
        print(f"❌ 전송 중 네트워크 에러: {e}")
        return None

def get_ticket_info():
    """구글 뉴스 RSS에서 중복 없이 티켓 정보 수집"""
    url = "https://news.google.com/rss/search?q=티켓+오픈+콘서트+페스티벌+전시&hl=ko&gl=KR&ceid=KR:ko"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser') 
        items = soup.find_all('item')
        
        found_events = []
        seen_titles = [] # 중복 방지용 리스트

        for item in items:
            title = item.title.text if item.title else ""
            
            # 링크 추출 (테스트 성공한 로직)
            link = ""
            if item.find('link'):
                link = item.find('link').next_element.strip()
            
            # 1. 키워드 필터링
            if any(kw in title for kw in KEYWORDS):
                clean_title = title.split(' - ')[0] # 언론사 이름 제거
                
                # 2. 중복 소식 방지 (제목 앞 10자 비교)
                short_title = clean_title[:10].replace(" ", "")
                if any(short_title in seen or seen in short_title for seen in seen_titles):
                    continue
                
                found_events.append(f"🎫 **{clean_title}**\n🔗 [자세히 보기]({link})")
                seen_titles.append(short_title)
            
            if len(found_events) >= 5: # 하루 최대 5개 소식
                break
        return found_events
    except Exception as e:
        print(f"❌ 수집 에러: {e}")
        return []

if __name__ == "__main__":
    if not TOKEN or not CHAT_ID:
        print("❌ 설정 에러: GitHub Secrets에서 TOKEN 또는 CHAT_ID를 찾을 수 없습니다.")
    else:
        print(f"🔍 티켓 정보 수집 및 전송 시작... (수신처: {CHAT_ID})")
        events = get_ticket_info()
        
        if events:
            msg = "📅 **오늘의 주요 티켓/공연 소식**\n"
            msg += "━━━━━━━━━━━━━━━\n\n"
            msg += "\n\n".join(events)
            
            result = send_telegram_message(msg)
            if result and result.get("ok"):
                print(f"✅ 전송 성공! ({len(events)}건)")
        else:
            print("✅ 새로운 소식이 없습니다.")
