import requests
from bs4 import BeautifulSoup
import os
import warnings

# SSL 경고 무시
warnings.filterwarnings("ignore")

# --- GitHub Secrets 설정 ---
TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

KEYWORDS = ["콘서트", "페스티벌", "내한", "전시", "오픈", "티켓", "공연", "뮤지컬"]

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
            print(f"❌ 텔레그램 서버 응답 에러: {res_data.get('description')}")
        return res_data
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
    """NOL티켓 API에서 콘서트 및 뮤지컬 정보 수집 (보강 버전)"""
    categories = ["CONCERT", "MUSICAL"]
    events = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Referer': 'https://nolticket.com/',
        'Origin': 'https://nolticket.com'
    }

    for cat in categories:
        try:
            # status=OPEN 필터를 제거하여 모든 상태의 상품을 확인
            url = f"https://api.nolticket.com/v1/product/list?category={cat}&page=0&size=10"
            print(f"🔍 NOL {cat} 데이터 요청 중...")
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                products = data.get('content', [])
                print(f"✅ NOL {cat} 수집 성공: {len(products)}건 발견")
                
                cat_name = "콘서트" if cat == "CONCERT" else "뮤지컬"
                
                count = 0
                for item in products:
                    name = item.get('name')
                    pid = item.get('id')
                    place = item.get('placeName', '장소미정')
                    sale_date = item.get('saleStartDate', '')
                    
                    link = f"https://nolticket.com/product/detail/{pid}"
                    
                    info_text = f"🎫 **[{cat_name}] {name}**\n📍 {place}"
                    if sale_date:
                        clean_date = sale_date.replace('T', ' ')[:16]
                        info_text += f"\n⏰ 오픈: {clean_date}"
                    
                    info_text += f"\n🔗 [예매하러가기]({link})"
                    events.append(info_text)
                    
                    count += 1
                    if count >= 3: break # 카테고리당 3개씩만
            else:
                print(f"❌ NOL {cat} 응답 에러: {response.status_code}")
                
        except Exception as e:
            print(f"❌ NOL {cat} 수집 중 에러: {e}")
            
    return events

if __name__ == "__main__":
    if not TOKEN or not CHAT_ID:
        print("❌ 설정 에러: GitHub Secrets(TOKEN, CHAT_ID)를 확인하세요.")
    else:
        print("🚀 통합 수집 시작 (Google News + NOL Ticket)")
        
        news_list = get_google_news()
        nol_list = get_nol_tickets()
        
        all_messages = news_list + nol_list
        
        if all_messages:
            final_msg = "📅 **오늘의 티켓 오픈 및 공연 소식**\n"
            final_msg += "━━━━━━━━━━━━━━━\n\n"
            final_msg += "\n\n".join(all_messages)
            
            result = send_telegram_message(final_msg)
            if result and result.get("ok"):
                print(f"✅ 최종 {len(all_messages)}건 전송 완료!")
        else:
            print("✅ 수집된 새로운 소식이 없습니다.")
