import requests
from bs4 import BeautifulSoup
import asyncio
import os
from telegram import Bot

# --- 설정 구간 ---
TOKEN = os.environ.get('TELEGRAM_TOKEN', '7874043423:AAEtpCMnZpG9lOzMHfwd1LxumLiAB-_oNAw')
CHAT_ID = os.environ.get('CHAT_ID', '-1003615231060') 

# 키워드를 조금 더 넓게 잡았습니다.
KEYWORDS = ["콘서트", "페스티벌", "내한", "전시", "오픈", "티켓", "공연"]

bot = Bot(token=TOKEN)

async def get_ticket_info():
    # 구글 뉴스 RSS 피드 (주소를 최신 형식으로 유지)
    url = "https://news.google.com/rss/search?q=티켓+오픈+콘서트+페스티벌+전시&hl=ko&gl=KR&ceid=KR:ko"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        # RSS는 XML 형식이므로 'xml' 파서를 쓰는 것이 가장 정확하지만, 
        # 없을 경우를 대비해 'html.parser'로 데이터를 강제로 읽습니다.
        soup = BeautifulSoup(response.content, 'html.parser') 
        
        # 구글 RSS의 각 항목은 <item> 태그 안에 있습니다.
        items = soup.find_all('item')
        print(f"📡 수집된 전체 뉴스 개수: {len(items)}개")
        
        found_events = []
        for item in items:
            title = item.title.text if item.title else ""
            link = item.link.text if item.link else ""
            
            # 키워드 매칭 확인
            if any(kw in title for kw in KEYWORDS):
                clean_title = title.split(' - ')[0]
                found_events.append(f"🎫 **{clean_title}**\n🔗 [자세히 보기]({link})")
            
            if len(found_events) >= 5: # 최대 5개까지만 수집
                break
                
        return found_events
    except Exception as e:
        print(f"❌ 데이터 수집 중 에러 발생: {e}")
        return []

async def main():
    if not TOKEN or not CHAT_ID:
        print("❌ 설정 에러: TOKEN 또는 CHAT_ID가 없습니다.")
        return

    print(f"🔍 티켓 정보 검색 시작... (대상 ID: {CHAT_ID})")
    events = await get_ticket_info()
    
    if events:
        msg = "📅 **오늘의 주요 티켓/공연 소식**\n"
        msg += "━━━━━━━━━━━━━━━\n\n"
        msg += "\n\n".join(events)
        
        try:
            await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown', disable_web_page_preview=True)
            print(f"✅ 텔레그램 전송 완료! ({len(events)}건)")
        except Exception as e:
            print(f"❌ 텔레그램 전송 실패: {e}")
    else:
        # 데이터가 없을 때 사용자에게 알림을 주기 위해 테스트 메시지 전송 (선택 사항)
        print("✅ 조건에 맞는 새로운 소식이 없습니다.")
        # 아래 주석을 해제하면 검색 결과가 없을 때도 메시지를 보냅니다.
        # await bot.send_message(chat_id=CHAT_ID, text="🔎 현재 키워드에 맞는 새로운 티켓 소식이 없습니다.")

if __name__ == "__main__":
    asyncio.run(main())
