import requests
from bs4 import BeautifulSoup
import os

# --- 설정 구간 ---
# 보안을 위해 TOKEN은 Secret에서 가져오고, CHAT_ID는 요청하신 대로 직접 설정합니다.
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = '-1003615231060' 

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
        return res.json()
    except Exception as e:
        print(f"❌ 텔레그램 전송 중 네트워크 에러: {e}")
        return None

def get_ticket_info():
    """구글 뉴스에서 티켓 정보를 수집하는 함수"""
    url = "https://news.google.com/rss/search?q=티켓+오픈+콘서트+페스티벌+전시&hl=ko&gl=KR&ceid=KR:ko"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        # GitHub 서버에서는 verify=False가 필요 없으므로 기본값으로 실행합니다.
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser') 
        items = soup.find_all('item')
        
        found_events = []
        for item in items:
            title = item.title.text if item.title else "제목 없음"
            
            # 링크 추출 보강 (방금 성공한 로직 반영)
            link = ""
            if item.find('link'):
                link = item.find('link').next_element.strip()
            
            # 키워드 매칭
            if any(kw in title for kw in KEYWORDS):
                clean_title = title.split(' - ')[0]
                found_events.append(f"🎫 **{clean_title}**\n🔗 [자세히 보기]({link})")
            
            if len(found_events) >= 10: # 최대 10개만 발송
                break
        return found_events
    except Exception as e:
        print(f"❌ 데이터 수집 중 에러 발생: {e}")
        return []

if __name__ == "__main__":
    if not TOKEN:
        print("❌ 에러: TELEGRAM_TOKEN이 설정되지 않았습니다.")
    else:
        print(f"🔍 티켓 정보 검색 시작... (수신처: {CHAT_ID})")
        events = get_ticket_info()
        
        if events:
            msg = "📅 **오늘의 주요 티켓/공연 소식**\n"
            msg += "━━━━━━━━━━━━━━━\n\n"
            msg += "\n\n".join(events)
            
            result = send_telegram_message(msg)
            if result and result.get("ok"):
                print("✅ 텔레그램 메시지 전송 성공!")
            else:
                print(f"❌ 전송 실패: {result}")
        else:
            print("✅ 새로운 공연 소식이 없습니다.")
