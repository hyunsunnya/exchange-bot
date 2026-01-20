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

def get_interpark_announcements():
    """인터파크 티켓 오픈 공지만 정확하게 수집"""
    # 쿼리: 인터파크 사이트 내에서 '티켓 오픈 공지'라는 단어가 포함된 최신 결과
    query = "site:ticket.interpark.com/Ticket/Goods/TPGoodsGate.asp \"티켓오픈공지\""
    url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
    
    events = []
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        items = soup.find_all('item')

        print(f"🔍 인터파크 공지 검색 중... {len(items)}건 발견")

        for item in items[:5]: # 최신 공지 5개
            title = item.title.text
            # 제목에서 불필요한 부분 정리
            clean_title = title.replace(" - 인터파크", "").replace("티켓오픈공지", "").strip()
            link = item.find('link').next_element.strip()
            
            # 실제 '놀 인터파크'로 연결되도록 링크 형태 살짝 변경 (선택 사항)
            # 기본 링크 그대로 사용해도 인터파크 페이지로 연결됩니다.
            events.append(f"📣 **[인터파크 공지]**\n{clean_title}\n🔗 [공지확인]({link})")
            
    except Exception as e:
        print(f"❌ 인터파크 수집 에러: {e}")
    
    return events

if __name__ == "__main__":
    if not TOKEN or not CHAT_ID:
        print("❌ 설정 에러: GitHub Secrets를 확인하세요.")
    else:
        print("🚀 인터파크 공지사항 추적 시작...")
        
        # 인터파크 공지사항 가져오기
        interpark_announcements = get_interpark_announcements()
        
        # 검색 결과가 너무 적을 경우를 대비해 일반 뉴스도 보강
        news_list = []
        try:
            news_query = "티켓 오픈 콘서트 뮤지컬"
            news_url = f"https://news.google.com/rss/search?q={news_query}&hl=ko&gl=KR&ceid=KR:ko"
            res = requests.get(news_url, timeout=10)
            soup = BeautifulSoup(res.content, 'html.parser')
            for item in soup.find_all('item')[:3]:
                news_list.append(f"📰 **[뉴스] {item.title.text.split(' - ')[0]}**\n🔗 [뉴스보기]({item.find('link').next_element.strip()})")
        except: pass

        all_messages = interpark_announcements + news_list
        
        if all_messages:
            final_msg = "📅 **오늘의 티켓 오픈 정보**\n"
            final_msg += "━━━━━━━━━━━━━━━\n\n"
            final_msg += "\n\n".join(all_messages)
            
            send_telegram_message(final_msg)
            print(f"✅ 총 {len(all_messages)}건 전송 성공!")
        else:
            print("✅ 수집된 정보가 없습니다.")
