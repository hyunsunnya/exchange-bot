import requests
from bs4 import BeautifulSoup
import asyncio
import os
from telegram import Bot

# --- 설정 구간 ---
# GitHub Secrets를 사용하거나, 로컬 테스트 시 직접 입력하세요.
TOKEN = os.environ.get('TELEGRAM_TOKEN', '7874043423:AAEtpCMnZpG9lOzMHfwd1LxumLiAB-_oNAw')
CHAT_ID = os.environ.get('CHAT_ID', '-1003615231060') 

# 관심 키워드
KEYWORDS = ["콘서트", "페스티벌", "내한", "전시", "오픈"]

bot = Bot(token=TOKEN)

async def get_ticket_info():
    # 구글 뉴스 RSS 피드 사용 (한국 공연 소식 키워드)
    url = "https://news.google.com/rss/search?q=티켓+오픈+콘서트+페스티벌+전시&hl=ko&gl=KR&ceid=KR:ko"
    
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')
        
        found_events = []
        for item in items[:15]:
            title = item.title.text
            link = item.link.text
            
            if any(kw in title for kw in KEYWORDS):
                # 뉴스 제목에서 불필요한 언론사 이름 제거 (보통 - 뒤에 붙음)
                clean_title = title.split(' - ')[0]
                found_events.append(f"🎫 **{clean_title}**\n🔗 [자세히 보기]({link})")
        return found_events
    except Exception as e:
        print(f"데이터 수집 에러: {e}")
        return []

async def main():
    if not TOKEN or not CHAT_ID:
        print("❌ 설정 에러: TOKEN 또는 CHAT_ID가 없습니다.")
        return

    print(f"🔍 티켓 정보 검색 중... (수신 ID: {CHAT_ID})")
    events = await get_ticket_info()
    
    if events:
        msg = "📅 **오늘의 주요 티켓/공연 소식**\n"
        msg += "━━━━━━━━━━━━━━━\n\n"
        msg += "\n\n".join(events[:5]) # 너무 길지 않게 상위 5개만 전송
        
        try:
            await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown', disable_web_page_preview=True)
            print("✅ 티켓 알림 전송 성공!")
        except Exception as e:
            print(f"❌ 전송 실패: {e}")
    else:
        print("✅ 현재 새로운 키워드 소식이 없습니다.")

if __name__ == "__main__":
    asyncio.run(main())
