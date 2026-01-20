import os
import warnings
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

warnings.filterwarnings("ignore")

# GitHub Secrets 로드
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

def send_telegram_message(text: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML", # HTML 모드 사용
        "disable_web_page_preview": True
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"❌ 텔레그램 전송 중 에러: {e}")
        return None

def get_ticket_data():
    queries = [
        ("📣 <b>[인터파크 공지]</b>", '인터파크 "티켓오픈공지"'),
        ("📰 <b>[티켓 뉴스]</b>", "티켓 오픈 콘서트 뮤지컬"),
    ]

    headers = {"User-Agent": "Mozilla/5.0"}
    all_events = []
    seen = set()

    for label, q in queries:
        q_encoded = quote(q)
        url = f"https://news.google.com/rss/search?q={q_encoded}&hl=ko&gl=KR&ceid=KR:ko"

        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()

            # 호환성을 위해 html.parser 사용
            soup = BeautifulSoup(res.content, "html.parser")
            items = soup.find_all('item')

            count = 0
            for item in items:
                title = item.title.text if item.title else "제목 없음"
                # RSS의 link 태그는 특이해서 아래 방식으로 추출하는 것이 가장 정확합니다.
                link = item.find('link').next_sibling.strip() if item.find('link') else ""
                
                # 중복 제거 (제목 앞 10자)
                clean_title = title.split(' - ')[0]
                short_title = clean_title[:10].replace(" ", "")

                if short_title not in seen:
                    # HTML 모드에 맞춰 태그 작성
                    all_events.append(f"{label}\n{clean_title}\n<a href='{link}'>🔗 자세히 보기</a>")
                    seen.add(short_title)
                    count += 1
                
                if count >= 5: break # 쿼리당 5개

        except Exception as e:
            print(f"❌ {label} 수집 중 에러: {e}")

    return all_events

if __name__ == "__main__":
    if not TOKEN or not CHAT_ID:
        print("❌ 설정 에러: GitHub Secrets를 확인하세요.")
    else:
        print("🚀 티켓 데이터 수집 및 전송 시작...")
        data = get_ticket_data()
        
        if data:
            # HTML 태그를 사용한 메시지 구성
            final_msg = "<b>📅 오늘의 티켓 오픈 및 공연 소식</b>\n"
            final_msg += "━━━━━━━━━━━━━━━\n\n"
            final_msg += "\n\n".join(data)
            
            send_telegram_message(final_msg)
            print(f"✅ 총 {len(data)}건 전송 성공!")
        else:
            print("✅ 새로운 소식이 없습니다.")
