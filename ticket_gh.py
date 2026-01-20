def get_nol_tickets():
    """NOL티켓 API에서 콘서트 및 뮤지컬 정보 수집 (보강 버전)"""
    # 카테고리별로 호출
    categories = ["CONCERT", "MUSICAL"]
    events = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Referer': 'https://nolticket.com/',
        'Accept': 'application/json, text/plain, */*'
    }

    for cat in categories:
        try:
            # 💡 status=OPEN을 제거하여 오픈 예정(READY) 등 모든 상태의 공연을 가져옵니다.
            url = f"https://api.nolticket.com/v1/product/list?category={cat}&page=0&size=10"
            print(f"🔗 NOL {cat} 데이터 요청 중...")
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # API 응답 구조에 따라 'content' 또는 'data' 확인
                products = data.get('content', [])
                
                cat_name = "콘서트" if cat == "CONCERT" else "뮤지컬"
                
                for item in products:
                    name = item.get('name')
                    pid = item.get('id')
                    place = item.get('placeName', '장소미정')
                    # 판매 시작일(오픈일) 정보 가져오기
                    sale_date = item.get('saleStartDate', '')
                    
                    link = f"https://nolticket.com/product/detail/{pid}"
                    
                    # 텍스트 구성 (오픈일 정보가 있으면 추가)
                    info_text = f"🎫 **[{cat_name}] {name}**\n📍 {place}"
                    if sale_date:
                        # 날짜 형식 정리 (예: 2024-05-20T14:00:00 -> 2024-05-20 14:00)
                        clean_date = sale_date.replace('T', ' ')[:16]
                        info_text += f"\n⏰ 오픈: {clean_date}"
                    
                    info_text += f"\n🔗 [예매하러가기]({link})"
                    events.append(info_text)
                    
                    # 카테고리당 최대 3개씩만 담기
                    if len([e for e in events if cat_name in e]) >= 3:
                        break
            else:
                print(f"❌ NOL {cat} 응답 실패: {response.status_code}")
                
        except Exception as e:
            print(f"❌ NOL {cat} 수집 중 에러: {e}")
            
    return events
