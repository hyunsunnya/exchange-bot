import requests
from bs4 import BeautifulSoup
import os
import warnings

# 경고 메시지 무시
warnings.filterwarnings("ignore")

# --- GitHub Secrets 설정 ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

KEYWORDS = ["콘서트", "페스티벌", "내한", "전시", "오픈", "티켓", "공연", "뮤지컬"]

def send_telegram_message(text):
    """텔레그램 메시지 전송"""
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

def get_google_news():
    """구글 뉴스에서 티켓 정보 수집"""
    url = "https://news.google.com/rss/search?q=티켓+오픈+콘서트+페스티벌+뮤지컬&hl=ko&gl=KR&ceid=KR:ko"
    events = []
    seen_titles = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser') 
        items = soup.find_all('item')
        
        for item in items:
            title = item.title.text if item.title else ""
            link = item.find('link').next_element.strip() if item.find('link') else ""
            
            if any(kw in title for kw in KEYWORDS):
                clean_title = title.split(' - ')[0]
                short_title = clean_title[:10].replace(" ", "")
                if not any(short_title in seen or seen in short_title for seen in seen_titles):
                    events.append(f"📰 **[뉴스] {clean_title}**\n🔗 [뉴스보기]({link})")
                    seen_titles.append(short_title)
            if len(events) >= 5: break
        return events
    except Exception as e:
        print(f"❌ 구글 뉴스 수집 실패: {e}")
        return []

def get_nol_tickets():
    """NOL티켓 API에서 콘서트 및 뮤지컬 정보 수집"""
    # 가져올 카테고리 리스트
    categories = ["CONCERT", "MUSICAL"]
    events = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Referer': 'https://nolticket.com/'
    }

    for cat in categories:
        try:
            # 카테고리별로 status=OPEN인 상품 5개씩 시도
            url = f"https://api.nolticket.com/v1/product/list?category={cat}&status=OPEN&page=0&size=5"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                products = response.json().get('content', [])
                cat_name = "콘서트" if cat == "CONCERT" else "뮤지컬"
                
                for item in products:
                    name = item.get('name')
                    pid = item.get('id')
                    place = item.get('placeName', '장소미정')
                    # 예매 시작일 정보가 있다면 포함
                    link = f"https://nolticket.com/product/detail/{pid}"
                    events.append(f"🎫 **[{cat_name}] {name}**\n📍 {place}\n🔗 [예매하러가기]({link})")
            
        except Exception as e:
            print(f"❌ NOL {cat} 수집 실패: {e}")
            
    return events

if __name__ == "__main__":
    if not TOKEN or not CHAT_ID:
        print("❌ 설정 에러: Secrets를 확인하세요.")
    else:
        print("🚀 통합 수집 시작 (뉴스 + NOL 콘서트/뮤지컬)")
        
        news_list = get_google_news()
        nol_list = get_nol_tickets()
        
        all_messages = news_list + nol_list
        
        if all_messages:
            final_msg = "📅 **오늘의 티켓 오픈 및 공연 소식**\n"
            final_msg += "━━━━━━━━━━━━━━━\n\n"
            final_msg += "\n\n".join(all_messages)
            
            result = send_telegram_message(final_msg)
            if result and result.get("ok"):
                print(f"✅ 총 {len(all_messages)}건 전송 완료!")
            else:
                print(f"❌ 텔레그램 전송 실패: {result}")
        else:
            print("✅ 새로운 소식이 없습니다.")
