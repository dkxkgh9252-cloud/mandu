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

async def fetch_all_exchanges():
    """
    모든 거래소(바이낸스, OKX, 바이비트, 비트겟, 게이트아이오, 빗썸, 업비트)의 시세를 
    비동기로 동시에 수집한 뒤 3가지 조건(해외↔해외, 국내←해외, 빗썸➔해외)을 계산합니다.
    """
    usd_krw = 1380.0  # 기본 적용 환율

    async with httpx.AsyncClient(timeout=6.0) as client:
        # 1. 모든 거래소 API 동시 요청
        tasks = [
            client.get("https://api.binance.com/api/v3/ticker/price"),               # 바이낸스
            client.get("https://www.okx.com/api/v5/market/tickers?instType=SPOT"),   # OKX
            client.get("https://api.bybit.com/v5/market/tickers?category=spot"),     # 바이비트
            client.get("https://api.bitget.com/api/v2/spot/market/tickers"),         # 비트겟
            client.get("https://api.gateio.ws/api/v4/spot/tickers"),                 # 게이트아이오
            client.get("https://api.bithumb.com/public/ticker/ALL_KRW"),             # 빗썸
            client.get("https://api.upbit.com/v1/ticker/all?quote_currencies=KRW")  # 업비트
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 2. 거래소별 데이터 파싱 저장소
        ex_prices = {} # ex_prices['Binance']['BTC'] = 65000.0

        # --- 바이낸스 파싱 ---
        if not isinstance(results[0], Exception) and results[0].status_code == 200:
            ex_prices['Binance'] = {}
            for item in results[0].json():
                if item['symbol'].endswith('USDT'):
                    sym = item['symbol'].replace('USDT', '')
                    ex_prices['Binance'][sym] = float(item['price'])

        # --- OKX 파싱 ---
        if not isinstance(results[1], Exception) and results[1].status_code == 200:
            ex_prices['OKX'] = {}
            for item in results[1].json().get('data', []):
                if item['instId'].endswith('-USDT'):
                    sym = item['instId'].replace('-USDT', '')
                    ex_prices['OKX'][sym] = float(item['last'])

        # --- 바이비트 파싱 ---
        if not isinstance(results[2], Exception) and results[2].status_code == 200:
            ex_prices['Bybit'] = {}
            for item in results[2].json().get('result', {}).get('list', []):
                if item['symbol'].endswith('USDT'):
                    sym = item['symbol'].replace('USDT', '')
                    ex_prices['Bybit'][sym] = float(item['lastPrice'])

        # --- 비트겟 파싱 ---
        if not isinstance(results[3], Exception) and results[3].status_code == 200:
            ex_prices['Bitget'] = {}
            for item in results[3].json().get('data', []):
                if item.get('symbol', '').endswith('USDT'):
                    sym = item['symbol'].replace('USDT', '')
                    ex_prices['Bitget'][sym] = float(item['lastPr'])

        # --- 게이트아이오 파싱 ---
        if not isinstance(results[4], Exception) and results[4].status_code == 200:
            ex_prices['Gate.io'] = {}
            for item in results[4].json():
                if item.get('currency_pair', '').endswith('_USDT'):
                    sym = item['currency_pair'].replace('_USDT', '')
                    ex_prices['Gate.io'][sym] = float(item['last'])

        # --- 빗썸 파싱 ---
        bithumb_prices = {}
        if not isinstance(results[5], Exception) and results[5].status_code == 200:
            b_data = results[5].json().get('data', {})
            for sym, val in b_data.items():
                if sym != 'date' and isinstance(val, dict):
                    bithumb_prices[sym] = float(val.get('closing_price', 0))

        # --- 업비트 파싱 ---
        upbit_prices = {}
        if not isinstance(results[6], Exception) and results[6].status_code == 200:
            for item in results[6].json():
                sym = item['market'].replace('KRW-', '')
                upbit_prices[sym] = float(item['trade_price'])

        global_list = []  # 해외 ↔ 해외
        inbound_list = [] # 국내 ← 해외 (업비트/빗썸)
        bithumb_list = [] # 빗썸 ➔ 해외

        foreign_exchanges = ['Binance', 'OKX', 'Bybit', 'Bitget', 'Gate.io']

        # 3. 차익 무제한 산출 로직
        # [1] 해외 ↔ 해외 차익
        for i in range(len(foreign_exchanges)):
            for j in range(len(foreign_exchanges)):
                if i == j: continue
                ex1, ex2 = foreign_exchanges[i], foreign_exchanges[j]
                if ex1 in ex_prices and ex2 in ex_prices:
                    for sym, p1 in ex_prices[ex1].items():
                        if sym in ex_prices[ex2] and p1 > 0:
                            p2 = ex_prices[ex2][sym]
                            profit = ((p2 - p1) / p1) * 100
                            if profit >= 1.0:
                                global_list.append({
                                    "symbol": sym,
                                    "buy_ex": ex1, "buy_price": f"${p1:,.4f}",
                                    "sell_ex": ex2, "sell_price": f"${p2:,.4f}",
                                    "profit": round(profit, 2)
                                })

        # [2] 국내(업비트/빗썸) ← 해외 차익
        domestics = [('Upbit', upbit_prices), ('Bithumb', bithumb_prices)]
        for dom_name, dom_dict in domestics:
            for f_ex in foreign_exchanges:
                if f_ex in ex_prices:
                    for sym, f_price in ex_prices[f_ex].items():
                        if sym in dom_dict and f_price > 0:
                            f_krw = f_price * usd_krw
                            d_price = dom_dict[sym]
                            profit = ((d_price - f_krw) / f_krw) * 100
                            if profit >= 1.0:
                                inbound_list.append({
                                    "symbol": sym,
                                    "buy_ex": f_ex, "buy_price": f"${f_price:,.4f}",
                                    "sell_ex": dom_name, "sell_price": f"{d_price:,.1f}원",
                                    "profit": round(profit, 2)
                                })

        # [3] 빗썸 ➔ 해외 차익
        for f_ex in foreign_exchanges:
            if f_ex in ex_prices:
                for sym, b_price in bithumb_prices.items():
                    if sym in ex_prices[f_ex] and b_price > 0:
                        f_price = ex_prices[f_ex][sym]
                        f_krw = f_price * usd_krw
                        profit = ((f_krw - b_price) / b_price) * 100
                        if profit >= 1.0:
                            bithumb_list.append({
                                "symbol": sym,
                                "buy_ex": "빗썸", "buy_price": f"{b_price:,.1f}원",
                                "sell_ex": f_ex, "sell_price": f"${f_price:,.4f}",
                                "profit": round(profit, 2)
                            })

        # 수익률 높은 순 정렬 (개수 제한 없이 전부 리턴)
        sort_fn = lambda lst: sorted(lst, key=lambda x: x["profit"], reverse=True)

        return {
            "global": sort_fn(global_list),
            "inbound": sort_fn(inbound_list),
            "bithumb": sort_fn(bithumb_list)
        }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await fetch_all_exchanges()
            await websocket.send_json(data)
            await asyncio.sleep(2.0)
    except WebSocketDisconnect:
        print("클라이언트 연결 종료")
    except Exception as e:
        print(f"웹소켓 에러: {e}")
