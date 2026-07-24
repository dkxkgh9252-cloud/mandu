import asyncio
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/")
async def get():
    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

async def get_arbitrage_data():
    """
    1% 이상 조건에 맞으면 개수 제한 없이 전부 리스트에 담아 리턴합니다.
    (수익률 높은 순 내림차순 정렬)
    """
    global_list = [
        {"symbol": "APT", "buy_ex": "Bybit", "buy_price": "$8.20", "sell_ex": "OKX", "sell_price": "$8.45", "profit": 3.04},
        {"symbol": "SUI", "buy_ex": "OKX", "buy_price": "$1.80", "sell_ex": "Bybit", "sell_price": "$1.85", "profit": 2.77},
        {"symbol": "NEAR", "buy_ex": "Binance", "buy_price": "$4.50", "sell_ex": "Bitget", "sell_price": "$4.62", "profit": 2.66},
        {"symbol": "PEPE", "buy_ex": "Binance", "buy_price": "$0.008", "sell_ex": "Gate.io", "sell_price": "$0.0082", "profit": 2.50},
        {"symbol": "SOL", "buy_ex": "Bybit", "buy_price": "$140", "sell_ex": "OKX", "sell_price": "$142.5", "profit": 1.78},
        {"symbol": "AVAX", "buy_ex": "OKX", "buy_price": "$25", "sell_ex": "Bybit", "sell_price": "$25.4", "profit": 1.60},
        {"symbol": "BTC", "buy_ex": "Binance", "buy_price": "$65,000", "sell_ex": "OKX", "sell_price": "$65,800", "profit": 1.23},
        {"symbol": "TIA", "buy_ex": "Binance", "buy_price": "$5.10", "sell_ex": "OKX", "sell_price": "$5.16", "profit": 1.18},
        {"symbol": "INJ", "buy_ex": "Bybit", "buy_price": "$18.5", "sell_ex": "OKX", "sell_price": "$18.7", "profit": 1.08},
        {"symbol": "RENDER", "buy_ex": "Binance", "buy_price": "$6.20", "sell_ex": "Bitget", "sell_price": "$6.26", "profit": 1.02},
    ]
    
    inbound_list = [
        {"symbol": "AVA", "buy_ex": "Bybit", "buy_price": "2,100원", "sell_ex": "Bithumb", "sell_price": "2,180원", "profit": 3.81},
        {"symbol": "SAND", "buy_ex": "Bybit", "buy_price": "420원", "sell_ex": "Upbit", "sell_price": "435원", "profit": 3.57},
        {"symbol": "MATIC", "buy_ex": "Binance", "buy_price": "600원", "sell_ex": "Bithumb", "sell_price": "615원", "profit": 2.50},
        {"symbol": "LINK", "buy_ex": "OKX", "buy_price": "18,000원", "sell_ex": "Upbit", "sell_price": "18,400원", "profit": 2.22},
        {"symbol": "XLM", "buy_ex": "Bybit", "buy_price": "130원", "sell_ex": "Upbit", "sell_price": "132원", "profit": 1.53},
        {"symbol": "ETH", "buy_ex": "Binance", "buy_price": "3,400,000원", "sell_ex": "Upbit", "sell_price": "3,450,000원", "profit": 1.47},
        {"symbol": "ALGO", "buy_ex": "Bybit", "buy_price": "180원", "sell_ex": "Upbit", "sell_price": "182.5원", "profit": 1.39},
        {"symbol": "STX", "buy_ex": "Binance", "buy_price": "2,100원", "sell_ex": "Bithumb", "sell_price": "2,125원", "profit": 1.19},
        {"symbol": "FLOW", "buy_ex": "OKX", "buy_price": "750원", "sell_ex": "Upbit", "sell_price": "758원", "profit": 1.07},
    ]
    
    bithumb_list = [
        {"symbol": "BONK", "buy_ex": "빗썸", "buy_price": "0.035원", "sell_ex": "OKX", "sell_price": "0.037원", "profit": 5.71},
        {"symbol": "SHIB", "buy_ex": "빗썸", "buy_price": "0.024원", "sell_ex": "OKX", "sell_price": "0.025원", "profit": 4.16},
        {"symbol": "XRP", "buy_ex": "빗썸", "buy_price": "850원", "sell_ex": "Binance", "sell_price": "880원", "profit": 3.52},
        {"symbol": "WIF", "buy_ex": "빗썸", "buy_price": "2,200원", "sell_ex": "Binance", "sell_price": "2,270원", "profit": 3.18},
        {"symbol": "SEI", "buy_ex": "빗썸", "buy_price": "450원", "sell_ex": "Bybit", "sell_price": "462원", "profit": 2.66},
        {"symbol": "DOGE", "buy_ex": "빗썸", "buy_price": "180원", "sell_ex": "Bybit", "sell_price": "183원", "profit": 1.66},
        {"symbol": "ADA", "buy_ex": "빗썸", "buy_price": "500원", "sell_ex": "Binance", "sell_price": "506원", "profit": 1.20},
        {"symbol": "EOS", "buy_ex": "빗썸", "buy_price": "780원", "sell_ex": "Bybit", "sell_price": "789원", "profit": 1.15},
        {"symbol": "TRX", "buy_ex": "빗썸", "buy_price": "170원", "sell_ex": "OKX", "sell_price": "171.8원", "profit": 1.06},
        {"symbol": "GALA", "buy_ex": "빗썸", "buy_price": "28원", "sell_ex": "Binance", "sell_price": "28.3원", "profit": 1.07},
    ]

    # 수익률 1.0% 이상인 것 전부 필터링 및 높은 순 정렬
    filter_and_sort = lambda lst: sorted([i for i in lst if i["profit"] >= 1.0], key=lambda x: x["profit"], reverse=True)

    return {
        "global": filter_and_sort(global_list),
        "inbound": filter_and_sort(inbound_list),
        "bithumb": filter_and_sort(bithumb_list)
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await get_arbitrage_data()
            await websocket.send_json(data)
            await asyncio.sleep(1.5)
    except WebSocketDisconnect:
        print("클라이언트 연결 종료")
    except Exception as e:
        print(f"웹소켓 에러: {e}")
