import os
import warnings
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from datetime import datetime

warnings.filterwarnings("ignore")

# GitHub Secrets 로드
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False # 링크 미리보기를 켜는 것이 신뢰도 확인에 좋습니다.
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"❌ 텔레그램 전송 중 에러: {e}")
        return None

def get_ticket_data():
    # tbs=qdr:d -> 최근 24시간 이내의 결과만 노출
    # tbs=qdr:h -> 최근 1시간 이내 (더 극단적인 최신성을 원할 경우)
    queries = [
        ("📣 <b>[인터파크 공지]</b>", '인터파크 "티켓 오픈 공지"'),
        ("📰 <b>[티켓 뉴스]</b>", "공연 티켓 오픈 콘서트 뮤지컬"),
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    all_events = []
    seen = set()

    for label, q in queries:
        q_encoded = quote(q)
        # &tbs=qdr:d 파라미터를 추가하여 24시간 이내 자료만 수집
        url = f"https://news.google.com/rss/search?q={q_encoded}+when:24h&hl=ko&gl=KR&ceid=KR:ko"

        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()

            # RSS는 xml 형식이므로 'xml' 파서가 좋지만, 기본 환경을 위해 'html.parser' 유지
            soup = BeautifulSoup(res.content, "html.parser")
            items = soup.find_all('item')

            count = 0
            for item in items:
                title = item.title.text if item.title else "제목 없음"
                # RSS 링크 추출 방식 개선 (가장 안전한 방식)
                link = item.link.text if item.link else ""
                
                # 중복 제거 및 클리닝
                clean_title = title.split(' - ')[0]
                short_title = clean_title[:12].replace(" ", "")

                if short_title not in seen:
                    # 게시글 시간 정보 가져오기 (선택 사항)
                    pub_date = item.pubdate.text if item.pubdate else ""
                    
                    msg = f"{label}\n{clean_title}\n<a href='{link}'>🔗 자세히 보기</a>"
                    all_events.append(msg)
                    seen.add(short_title)
                    count += 1
                
                if count >= 5: break 

        except Exception as e:
            print(f"❌ {label} 수집 중 에러: {e}")

    return all_events

if __name__ == "__main__":
    if not TOKEN or not CHAT_ID:
        print("❌ 설정 에러: GitHub Secrets를 확인하세요.")
    else:
        print(f"🚀 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 수집 시작...")
        data = get_ticket_data()
        
        if data:
            final_msg = f"<b>📅 {datetime.now().strftime('%m/%d')} 티켓 오픈 소식</b>\n"
            final_msg += "━━━━━━━━━━━━━━━\n\n"
            final_msg += "\n\n".join(data)
            
            send_telegram_message(final_msg)
            print(f"✅ 총 {len(data)}건 전송 성공!")
        else:
            print("✅ 최근 24시간 내에 새로운 소식이 없습니다.")
