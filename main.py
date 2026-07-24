import asyncio
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# 빗썸 & 타 거래소 데이터 파싱 함수 (예시 구조 - 비동기 에러 방지)
async def fetch_prices():
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            # 빗썸 티커 조회
            response = await client.get("https://api.bithumb.com/public/ticker/ALL_KRW")
            data = response.json()
            return data
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None

@app.get("/")
async def get():
    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # 1.3초마다 실시간 업데이트
            await asyncio.sleep(1.3)
            
            # 파일에서 html 읽어오기 또는 데이터 바인딩
            with open("index.html", "r", encoding="utf-8") as f:
                html_content = f.read()
                
            await websocket.send_text(html_content)
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket Error: {e}")
