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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    async with httpx.AsyncClient(timeout=10.0, headers=headers, follow_redirects=True) as client:
        tasks = [
            client.get("https://api.binance.com/api/v3/ticker/price"),
            client.get("https://www.okx.com/api/v5/market/tickers?instType=SPOT"),
            client.get("https://api.bybit.com/v5/market/tickers?category=spot"),
            client.get("https://api.bitget.com/api/v2/spot/market/tickers"),
            client.get("https://api.gateio.ws/api/v4/spot/tickers"),
            client.get("https://api.bithumb.com/public/ticker/ALL_KRW"),
            client.get("https://api.upbit.com/v1/ticker/all?quote_currencies=KRW"),
            client.get("https://api.bithumb.com/public/assets_status/ALL")
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        foreign_prices = {}
        if not isinstance(results[0], Exception) and results[0].status_code == 200:
            foreign_prices['바이낸스'] = {i['symbol'].replace('USDT', '').upper(): float(i['price']) for i in results[0].json() if i['symbol'].endswith('USDT') and float(i['price']) > 0.0001}

        if not isinstance(results[1], Exception) and results[1].status_code == 200:
            foreign_prices['OKX'] = {i['instId'].replace('-USDT', '').upper(): float(i['last']) for i in results[1].json().get('data', []) if i['instId'].endswith('-USDT') and float(i['last']) > 0.0001}

        if not isinstance(results[2], Exception) and results[2].status_code == 200:
            foreign_prices['바이비트'] = {i['symbol'].replace('USDT', '').upper(): float(i['lastPrice']) for i in results[2].json().get('result', {}).get('list', []) if i['symbol'].endswith('USDT') and float(i['lastPrice']) > 0.0001}

        if not isinstance(results[3], Exception) and results[3].status_code == 200:
            foreign_prices['비트겟'] = {i['symbol'].replace('USDT', '').upper(): float(i['lastPr']) for i in results[3].json().get('data', []) if i.get('symbol', '').endswith('USDT') and float(i.get('lastPr', 0)) > 0.0001}

        if not isinstance(results[4], Exception) and results[4].status_code == 200:
            foreign_prices['게이트아이오'] = {i['currency_pair'].replace('_USDT', '').upper(): float(i['last']) for i in results[4].json() if i.get('currency_pair', '').endswith('_USDT') and float(i.get('last', 0)) > 0.0001}

        bithumb_prices = {}
        usd_krw = 1462.0
        
        if not isinstance(results[5], Exception) and results[5].status_code == 200:
            try:
                b_data = results[5].json().get('data', {})
                for sym, val in b_data.items():
                    if sym != 'date' and isinstance(val, dict):
                        p = float(val.get('closing_price', 0))
                        if p > 0.1:
                            bithumb_prices[sym.upper()] = p
                if 'USDT' in bithumb_prices:
                    usd_krw = bithumb_prices['USDT']
            except Exception:
                pass

        upbit_prices = {}
        if not isinstance(results[6], Exception) and results[6].status_code == 200:
            try:
                upbit_prices = {i['market'].replace('KRW-', '').upper(): float(i['trade_price']) for i in results[6].json() if float(i['trade_price']) > 0.1}
            except Exception:
                pass

        bithumb_withdraw_block = set()
        if not isinstance(results[7], Exception) and results[7].status_code == 200:
            try:
                bs_data = results[7].json().get('data', {})
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

        for sym, b_price in bithumb_prices.items():
            if sym == 'USDT' or sym in bithumb_withdraw_block:
                continue

            best_sell_ex = ""
            best_sell_price_krw = 0
            best_profit = -999.0

            if sym in upbit_prices:
                u_price = upbit_prices[sym]
                profit = ((u_price - b_price) / b_price) * 100
                if profit > best_profit:
                    best_profit = profit
                    best_sell_ex = "업비트"
                    best_sell_price_krw = u_price

            for f_name, f_dict in foreign_prices.items():
                if sym in f_dict:
                    f_price_krw = f_dict[sym] * usd_krw
                    profit = ((f_price_krw - b_price) / b_price) * 100
                    if profit > best_profit:
                        best_profit = profit
                        best_sell_ex = f_name
                        best_sell_price_krw = f_price_krw

            if 1.0 <= best_profit <= 50.0:
                all_items.append({
                    "symbol": sym,
                    "bithumb_price": format_krw(b_price),
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
