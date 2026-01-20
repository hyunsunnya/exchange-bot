import requests
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

def get_interpark_ranking():
    """인터파크 티켓의 실시간 랭킹 데이터를 직접 수집 (더 정확함)"""
    # 콘서트(01003) 및 뮤지컬(01011) 장르 랭킹 API
    genres = {"콘서트": "01003", "뮤지컬": "01011"}
    events = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }

    for name, code in genres.items():
        try:
            # 인터파크 랭킹 데이터 경로
            url = f"http://ticket.interpark.com/api/ranking/genre?genreCode={code}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # 랭킹 상위 3개씩만 추출
                items = data.get('data', [])[:3]
                for item in items:
                    title = item.get('productName')
                    place = item.get('placeName')
                    p_code = item.get('productCode')
                    # 놀 인터파크 상세 페이지 주소로 조합
                    link = f"https://nol.interpark.com/product/detail/{p_code}"
                    
                    events.append(f"🎫 **[{name}] {title}**\n📍 {place}\n🔗 [예매하러가기]({link})")
            print(f"✅ 인터파크 {name} 수집 완료")
        except Exception as e:
            print(f"❌ 인터파크 {name} 수집 중 에러: {e}")
            
    return events

if __name__ == "__main__":
    if not TOKEN or not CHAT_ID:
        print("❌ 설정 에러: GitHub Secrets를 확인하세요.")
    else:
        print("🚀 인터파크 데이터 직결 수집 시작...")
        
        # 1. 인터파크 랭킹 정보 (매우 정확)
        interpark_list = get_interpark_ranking()
        
        # 2. 만약을 위해 일반 뉴스도 2개만 섞기
        news_list = []
        try:
            news_url = "https://news.google.com/rss/search?q=티켓+오픈+콘서트+뮤지컬&hl=ko&gl=KR&ceid=KR:ko"
            res = requests.get(news_url, timeout=10)
            soup = BeautifulSoup(res.content, 'html.parser')
            for item in soup.find_all('item')[:2]:
                news_list.append(f"📰 **[뉴스] {item.title.text.split(' - ')[0]}**\n🔗 [뉴스보기]({item.find('link').next_element.strip()})")
        except: pass

        all_messages = interpark_list + news_list
        
        if all_messages:
            final_msg = "📅 **오늘의 인기 티켓 & 오픈 정보**\n"
            final_msg += "━━━━━━━━━━━━━━━\n\n"
            final_msg += "\n\n".join(all_messages)
            
            send_telegram_message(final_msg)
            print(f"✅ 총 {len(all_messages)}건 전송 완료!")
        else:
            print("✅ 새로운 소식이 없습니다.")
