import requests
from bs4 import BeautifulSoup
import os

# --- 설정 구간 ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = '-1003615231060' 

KEYWORDS = ["콘서트", "페스티벌", "내한", "전시", "오픈", "티켓", "공연"]

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

def get_ticket_info():
    url = "https://news.google.com/rss/search?q=티켓+오픈+콘서트+페스티벌+전시&hl=ko&gl=KR&ceid=KR:ko"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser') 
        items = soup.find_all('item')
        
        found_events = []
        seen_titles = [] # 이미 처리한 기사 키워드를 저장

        for item in items:
            title = item.title.text if item.title else ""
            link = ""
            if item.find('link'):
                link = item.find('link').next_element.strip()
            
            # 1. 키워드 포함 여부 확인
            if any(kw in title for kw in KEYWORDS):
                clean_title = title.split(' - ')[0] # 언론사명 제거
                
                # 2. 중복 방지 로직: 제목의 앞 10글자가 이미 저장된 제목들과 겹치는지 확인
                # (보통 같은 행사 기사는 제목 앞부분이 비슷합니다)
                short_title = clean_title[:10].replace(" ", "")
                if any(short_title in seen or seen in short_title for seen in seen_titles):
                    continue # 비슷한 제목이 이미 있다면 건너뜀
                
                found_events.append(f"🎫 **{clean_title}**\n🔗 [자세히 보기]({link})")
                seen_titles.append(short_title) # 새로운 제목 키워드 등록
            
            if len(found_events) >= 5:
                break
        return found_events
    except Exception as e:
        print(f"❌ 데이터 수집 에러: {e}")
        return []

if __name__ == "__main__":
    if not TOKEN:
        print("❌ 에러: TELEGRAM_TOKEN이 설정되지 않았습니다.")
    else:
        print(f"🔍 중복 제거 필터 적용 중... (수신처: {CHAT_ID})")
        events = get_ticket_info()
        
        if events:
            msg = "📅 **오늘의 주요 티켓/공연 소식**\n"
            msg += "━━━━━━━━━━━━━━━\n\n"
            msg += "\n\n".join(events)
            
            send_telegram_message(msg)
            print(f"✅ 중복 제외 {len(events)}건 전송 완료!")
        else:
            print("✅ 새로운 소식이 없습니다.")
