import os
import warnings
import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import quote
from datetime import datetime

# SSL 경고 및 일반 경고 무시
warnings.filterwarnings("ignore")
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# [설정] 직접 입력된 값 유지
TOKEN = "7874043423:AAEtpCMnZpG9lOzMHfwd1LxumLiAB-_oNAw"
CHAT_ID = "-1003615231060"

def send_telegram_message(text: str):
    """텔레그램 메시지 전송 (재시도 로직 포함)"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    
    for i in range(3): # 최대 3번 재시도
        try:
            res = requests.post(url, json=payload, timeout=20, verify=False)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"⚠️ 재시도 {i+1}: {e}")
            time.sleep(5)
    return None

def get_ticket_data():
    """구글 뉴스 RSS 데이터 수집 및 링크 정리"""
    queries = [
        ("📣 <b>[인터파크 공지]</b>", '인터파크 "티켓 오픈 공지"'),
        ("📰 <b>[티켓 뉴스]</b>", "공연 티켓 오픈 콘서트 뮤지컬"),
    ]

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"}
    all_events = []
    seen = set()

    for label, q in queries:
        # when:1d로 최근 24시간 필터링
        q_encoded = quote(f"{q} when:1d")
        url = f"https://news.google.com/rss/search?q={q_encoded}&hl=ko&gl=KR&ceid=KR:ko"

        try:
            res = requests.get(url, headers=headers, timeout=15, verify=False)
            res.raise_for_status()
            soup = BeautifulSoup(res.content, "html.parser")
            items = soup.find_all('item')

            count = 0
            for item in items:
                title = item.title.text if item.title else "제목 없음"
                
                # 링크 추출
                link_tag = item.find('link')
                raw_link = ""
                if link_tag:
                    raw_link = link_tag.text.strip() if link_tag.text else link_tag.next_sibling.strip()
                
                if not raw_link: continue

                clean_title = title.split(' - ')[0]
                short_title = clean_title[:15].replace(" ", "")

                if short_title not in seen:
                    # [링크 최적화] 복잡한 URL은 '🔗 자세히 보기' 뒤에 숨김
                    # 따옴표 에러 방지를 위해 간단한 처리 추가
                    safe_link = raw_link.replace('"', '').replace("'", "")
                    event_msg = f"{label}\n<b>{clean_title}</b>\n<a href='{safe_link}'>🔗 자세히 보기</a>"
                    
                    all_events.append(event_msg)
                    seen.add(short_title)
                    count += 1
                
                if count >= 5: break 

        except Exception as e:
            print(f"❌ {label} 수집 중 에러: {e}")

    return all_events

if __name__ == "__main__":
    print(f"🚀 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 데이터 수집 시작...")
    data = get_ticket_data()
    
    if data:
        header = f"<b>📅 {datetime.now().strftime('%m월 %d일')} 티켓 소식</b>\n"
        header += "━━━━━━━━━━━━━━━━━━\n\n"
        final_msg = header + "\n\n".join(data)
        
        if len(final_msg) > 4000:
            final_msg = final_msg[:3900] + "\n\n...(이하 생략)"

        success = send_telegram_message(final_msg)
        if success:
            print(f"✅ 총 {len(data)}건 전송 성공!")
    else:
        print("✅ 최근 24시간 내 새로운 소식이 없습니다.")
