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

async def fetch_bithumb_arbitrage():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    async with httpx.AsyncClient(timeout=15.0, headers=headers, follow_redirects=True) as client:
        # 프록시 및 각 거래소 호가창(Orderbook) API 엔드포인트
        binance_proxy = "https://api.allorigins.win/raw?url=https://api.binance.com/api/v3/ticker/bookTicker"
        bybit_proxy = "https://api.allorigins.win/raw?url=https://api.bybit.com/v5/market/tickers?category=spot"

        tasks = [
            client.get(binance_proxy),
            client.get(bybit_proxy),
            client.get("https://api.bitget.com/api/v2/spot/market/tickers"),
            client.get("https://api.bithumb.com/public/orderbook/ALL_KRW"),
            client.get("https://api.upbit.com/v1/orderbook?markets=" + ",".join([f"KRW-{s}" for s in ["BTC", "ETH", "XRP", "SOL", "ADA", "DOGE", "AVAX", "DOT", "LINK", "MATIC", "NEAR", "ATOM", "ETC", "BCH", "UNI", "XLM", "ICP", "APT", "SUI", "STX", "ARB", "IMX", "SEI", "NEAR", "FIL", "FLOW", "SAND", "MANA", "CHZ", "AXS", "ENJ", "THETA", "EOS", "KAVA", "ZIL", "ICX", "ONT", "QTUM", "WEMIX", "CRO", "ELF", "IOST", "SRM", "MVL", "ORBS", "MED", "META", "BORA", "API3", "PLA", "POWR", "GLM", "AQT", "MLK", "ASR", "JUV", "PSG", "ATM", "HERO", "PCI", "CONV", "OBSR", "SOMESING", "AMO", "WINGS", "DAD", "TRV", "TEMCO", "BP", "ORC", "GOM2", "VALOR", "PCI", "BIOT", "DAT", "BAO", "MBX", "IO", "TURBO", "BLUR", "MEME", "PEPE", "WIF", "BONK", "FLOKI", "BOME", "NOT", "CATI", "HMSTR", "SUI", "TIA", "PYTH", "JUP", "ZETA", "MANTA", "ALT", "STRK", "AEVO", "ENA", "SAGA", "BB", "REZ", "IO", "ZK", "LISTA", "BANANA", "RENDER", "TON", "S", "XRP"]])), # 주요 코인 업비트 오더북 대상
            client.get("https://api.bithumb.com/public/assets_status/ALL")
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        foreign_ask_prices = {}
        
        # 1. 바이낸스 (bookTicker: askPrice = 최우선 매도호가)
        if not isinstance(results[0], Exception) and results[0].status_code == 200:
            try:
                b_data = results[0].json()
                if isinstance(b_data, list):
                    foreign_ask_prices['바이낸스'] = {
                        i['symbol'].replace('USDT', '').upper(): float(i['askPrice']) 
                        for i in b_data if i['symbol'].endswith('USDT') and float(i['askPrice']) > 0
                    }
            except Exception:
                pass

        # 2. 바이비트 (ask1Price = 최우선 매도호가)
        if not isinstance(results[1], Exception) and results[1].status_code == 200:
            try:
                bybit_json = results[1].json()
                bybit_list = bybit_json.get('result', {}).get('list', [])
                foreign_ask_prices['바이비트'] = {
                    i['symbol'].replace('USDT', '').upper(): float(i['ask1Price']) 
                    for i in bybit_list if i['symbol'].endswith('USDT') and float(i['ask1Price']) > 0
                }
            except Exception:
                pass

        # 3. 비트겟 (askPr = 최우선 매도호가)
        if not isinstance(results[2], Exception) and results[2].status_code == 200:
            try:
                bitget_json = results[2].json()
                foreign_ask_prices['비트겟'] = {
                    i['symbol'].replace('USDT', '').upper(): float(i['askPr']) 
                    for i in bitget_json.get('data', []) if i.get('symbol', '').endswith('USDT') and float(i.get('askPr', 0)) > 0
                }
            except Exception:
                pass

        # 4. 빗썸 오더북 (빗썸에서 살 때는 매도호가(asks)의 가장 낮은 가격 기준)
        bithumb_buy_prices = {}
        usd_krw = 1462.0
        if not isinstance(results[3], Exception) and results[3].status_code == 200:
            try:
                b_data = results[3].json().get('data', {})
                for sym, val in b_data.items():
                    if sym != 'date' and isinstance(val, dict):
                        asks = val.get('asks', [])
                        if asks and isinstance(asks, list):
                            p = float(asks[0].get('price', 0)) # 최우선 매도호가
                            if p > 0:
                                bithumb_buy_prices[sym.upper()] = p
                if 'USDT' in bithumb_buy_prices:
                    usd_krw = bithumb_buy_prices['USDT']
            except Exception:
                pass

        # 5. 업비트 오더북 (업비트에서 팔 때는 매수호가(bids)의 가장 높은 가격 기준)
        upbit_sell_prices = {}
        if not isinstance(results[4], Exception) and results[4].status_code == 200:
            try:
                for item in results[4].json():
                    market = item.get('market', '').replace('KRW-', '').upper()
                    orderbook_units = item.get('orderbook_units', [])
                    if orderbook_units:
                        best_bid = float(orderbook_units[0].get('bid_price', 0)) # 최우선 매수호가
                        if best_bid > 0:
                            upbit_sell_prices[market] = best_bid
            except Exception:
                pass

        # 6. 빗썸 출금 상태
        bithumb_withdraw_block = set()
        if not isinstance(results[5], Exception) and results[5].status_code == 200:
            try:
                bs_data = results[5].json().get('data', {})
                for sym, status in bs_data.items():
                    if isinstance(status, dict):
                        if str(status.get('withdrawal_status', '1')) == '0':
                            bithumb_withdraw_block.add(sym.upper())
            except Exception:
                pass

        all_items = []

        def format_krw(price):
            if price < 1: return f"{price:.5f}원"
            if price < 100: return f"{price:.2f}원"
            return f"{price:,.0f}원"

        for sym, b_buy_price in bithumb_buy_prices.items():
            if sym == 'USDT' or sym in bithumb_withdraw_block:
                continue

            best_sell_ex = ""
            best_sell_price_krw = 0
            best_profit = -999.0

            # 업비트 비교 (업비트 매수호가 기준)
            if sym in upbit_sell_prices:
                u_price = upbit_sell_prices[sym]
                profit = ((u_price - b_buy_price) / b_buy_price) * 100
                if profit > best_profit:
                    best_profit = profit
                    best_sell_ex = "업비트"
                    best_sell_price_krw = u_price

            # 해외 거래소 비교 (해외 매도호가 * 환율 기준)
            for f_name, f_dict in foreign_ask_prices.items():
                if sym in f_dict:
                    f_price_krw = f_dict[sym] * usd_krw
                    profit = ((f_price_krw - b_buy_price) / b_buy_price) * 100
                    if profit > best_profit:
                        best_profit = profit
                        best_sell_ex = f_name
                        best_sell_price_krw = f_price_krw

            if 1.0 <= best_profit <= 50.0:
                all_items.append({
                    "symbol": sym,
                    "bithumb_price": format_krw(b_buy_price),
                    "sell_ex": best_sell_ex,
                    "sell_price": format_krw(best_sell_price_krw),
                    "profit": round(best_profit, 2)
                })

        return {
            "usdt_krw": f"{usd_krw:,.0f}",
            "high": all_items,
            "normal": []
        }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await fetch_bithumb_arbitrage()
            await websocket.send_json(data)
            await asyncio.sleep(2.0)
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
