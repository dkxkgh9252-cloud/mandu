import asyncio
import json
import httpx
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>빗썸 출발 전체 코인 실시간 차익 스캐너 (2단 그리드 & 1.5% 강조)</title>
    <style>
        body { background-color: #121212; color: #fff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; }
        h1 { text-align: center; color: #ff9800; margin-bottom: 5px; }
        .subtitle { text-align: center; color: #888; font-size: 0.9rem; margin-bottom: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        
        /* 2단 분할 레이아웃 */
        .grid-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .column-card {
            background: #1e1e1e;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            border: 1px solid #2d2d2d;
        }

        .column-title {
            font-size: 1.1rem;
            font-weight: bold;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 2px solid #333;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .high-title { color: #ff9800; border-bottom-color: #ff9800; }
        .mid-title { color: #00e676; border-bottom-color: #00e676; }

        table { width: 100%; border-collapse: collapse; margin-top: 5px; }
        th, td { padding: 10px 12px; text-align: center; border-bottom: 1px solid #2d2d2d; }
        th { background-color: #252525; color: #aaa; font-weight: 600; font-size: 0.8rem; position: sticky; top: 0; }
        tr:hover { background-color: #2a2a2a; }

        .symbol { font-weight: bold; font-size: 1rem; color: #fff; }
        .badge { padding: 3px 6px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }
        .buy-bg { background-color: rgba(255, 152, 0, 0.15); color: #ff9800; border: 1px solid #ff9800; }
        .sell-bg { background-color: rgba(33, 150, 243, 0.15); color: #2196f3; border: 1px solid #2196f3; }
        
        .rate { font-size: 1rem; font-weight: bold; }
        .plus-green { color: #00e676; }
        
        /* 1.5% 이상 주황색 스타일 하이라이트 */
        .highlight-orange {
            background-color: rgba(255, 152, 0, 0.08);
        }
        .highlight-orange .symbol { color: #ffb74d; }
        .rate-orange { color: #ff9800 !important; font-size: 1.1rem; font-weight: 800; }

        @media (max-width: 900px) {
            .grid-container { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>

<div class="container">
    <h1>🚀 빗썸 출발 전체 코인 차익 스캐너</h1>
    <div class="subtitle">기준 USDT 가격 (빗썸): <span id="usdt-rate" style="color:#ff9800; font-weight:bold;">-</span> KRW | 필터: <strong>빗썸 출금 가능 & 1.0% 이상</strong></div>

    <div class="grid-container">
        <!-- 1.5% 이상 (좌측 주황색 강조) -->
        <div class="column-card">
            <div class="column-title high-title">
                <span>🔥 고수익 구간 (1.5% 이상)</span>
                <span id="high-count" style="font-size:0.9rem;">0개</span>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>코인</th>
                        <th>빗썸 (매수 1호가)</th>
                        <th>최고가 매도처</th>
                        <th>기대 수익률</th>
                    </tr>
                </thead>
                <tbody id="list-high">
                    <tr><td colspan="4" style="text-align:center; padding: 30px; color: #888;">탐색 중...</td></tr>
                </tbody>
            </table>
        </div>

        <!-- 1.0% ~ 1.5% 미만 (우측) -->
        <div class="column-card">
            <div class="column-title mid-title">
                <span>⚡ 일반 구간 (1.0% ~ 1.5% 미만)</span>
                <span id="mid-count" style="font-size:0.9rem;">0개</span>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>코인</th>
                        <th>빗썸 (매수 1호가)</th>
                        <th>최고가 매도처</th>
                        <th>기대 수익률</th>
                    </tr>
                </thead>
                <tbody id="list-mid">
                    <tr><td colspan="4" style="text-align:center; padding: 30px; color: #888;">탐색 중...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
</div>

<script>
    const ws = new WebSocket(`ws://${location.host}/ws`);

    function formatPrice(price) {
        if (price < 1) return price.toFixed(5);      
        if (price < 100) return price.toFixed(2);    
        return Math.round(price).toLocaleString();  
    }

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        document.getElementById("usdt-rate").innerText = data.usdt_krw.toLocaleString();

        const listHigh = document.getElementById("list-high");
        const listMid = document.getElementById("list-mid");

        listHigh.innerHTML = "";
        listMid.innerHTML = "";

        let highCount = 0;
        let midCount = 0;

        data.opportunities.forEach(item => {
            const tr = document.createElement("tr");

            if (item.profit_rate >= 1.5) {
                highCount++;
                tr.className = "highlight-orange";
                tr.innerHTML = `
                    <td class="symbol">${item.symbol}</td>
                    <td><span style="font-size:0.85rem; color:#ccc;">${formatPrice(item.buy_price)} 원</span></td>
                    <td>
                        <span class="badge sell-bg">${item.sell_ex}</span><br>
                        <span style="font-size:0.85rem; color:#ccc;">${formatPrice(item.sell_price)} 원</span>
                    </td>
                    <td class="rate rate-orange">+${item.profit_rate.toFixed(2)}%</td>
                `;
                listHigh.appendChild(tr);
            } else {
                midCount++;
                tr.innerHTML = `
                    <td class="symbol">${item.symbol}</td>
                    <td><span style="font-size:0.85rem; color:#ccc;">${formatPrice(item.buy_price)} 원</span></td>
                    <td>
                        <span class="badge sell-bg">${item.sell_ex}</span><br>
                        <span style="font-size:0.85rem; color:#ccc;">${formatPrice(item.sell_price)} 원</span>
                    </td>
                    <td class="rate plus-green">+${item.profit_rate.toFixed(2)}%</td>
                `;
                listMid.appendChild(tr);
            }
        });

        document.getElementById("high-count").innerText = highCount + "개";
        document.getElementById("mid-count").innerText = midCount + "개";

        if (highCount === 0) {
            listHigh.innerHTML = `<tr><td colspan="4" style="text-align:center; padding: 30px; color: #888;">1.5% 이상 코인이 없습니다.</td></tr>`;
        }
        if (midCount === 0) {
            listMid.innerHTML = `<tr><td colspan="4" style="text-align:center; padding: 30px; color: #888;">1.0% ~ 1.5% 미만 코인이 없습니다.</td></tr>`;
        }
    };
</script>

</body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(content=HTML_LAYOUT)

async def fetch_prices():
    async with httpx.AsyncClient(timeout=5.0) as client:
        bithumb_buy_prices = {}
        usdt_krw = 1463.0

        # 1. 빗썸 출금 상태 및 호가창 조회
        try:
            status_res = await client.get("https://api.bithumb.com/public/assetsstatus/ALL")
            status_data = status_res.json().get("data", {})

            res = await client.get("https://api.bithumb.com/public/orderbook/ALL_KRW")
            bdata = res.json().get("data", {})
            
            for coin, info in bdata.items():
                if coin != "timestamp" and isinstance(info, dict) and "asks" in info and len(info["asks"]) > 0:
                    coin_status = status_data.get(coin, {})
                    can_withdraw = coin_status.get("withdrawal_status", 0) == 1

                    if can_withdraw:
                        ask_price = float(info["asks"][0]["price"])
                        if ask_price > 0:
                            bithumb_buy_prices[coin] = ask_price

            if "USDT" in bithumb_buy_prices:
                usdt_krw = bithumb_buy_prices["USDT"]
        except Exception as e:
            print("Bithumb API Error:", e)

        upbit_sell_prices = {}
        binance_sell_prices = {}
        bybit_sell_prices = {}
        gate_sell_prices = {}

        # 2. 업비트 호가창 조회
        try:
            m_res = await client.get("https://api.upbit.com/v1/market/all?isDetails=false")
            krw_markets = [item["market"] for item in m_res.json() if item["market"].startswith("KRW-")]
            
            for i in range(0, len(krw_markets), 100):
                chunk = krw_markets[i:i+100]
                ob_res = await client.get(f"https://api.upbit.com/v1/orderbook?markets={','.join(chunk)}")
                for item in ob_res.json():
                    coin = item["market"].split("-")[1]
                    if item.get("orderbook_units") and len(item["orderbook_units"]) > 0:
                        bid_price = float(item["orderbook_units"][0]["bid_price"])
                        if bid_price > 0:
                            upbit_sell_prices[coin] = bid_price
        except Exception as e:
            print("Upbit Error:", e)

        # 3. 바이낸스 최상단 호가 조회
        try:
            res = await client.get("https://api.binance.com/api/v3/ticker/bookTicker")
            for item in res.json():
                symbol = item["symbol"]
                bid_price = float(item.get("bidPrice", 0))
                bid_qty = float(item.get("bidQty", 0))
                if symbol.endswith("USDT") and bid_price > 0 and bid_qty > 0:
                    coin = symbol[:-4]
                    binance_sell_prices[coin] = bid_price * usdt_krw
        except Exception as e:
            print("Binance Error:", e)

        # 4. 바이비트 최상단 호가 조회
        try:
            res = await client.get("https://api.bybit.com/v5/market/tickers?category=spot")
            for item in res.json()["result"]["list"]:
                symbol = item["symbol"]
                bid_price = float(item.get("bid1Price", 0))
                bid_size = float(item.get("bid1Size", 0))
                if symbol.endswith("USDT") and bid_price > 0 and bid_size > 0:
                    coin = symbol[:-4]
                    bybit_sell_prices[coin] = bid_price * usdt_krw
        except Exception as e:
            print("Bybit Error:", e)

        # 5. 게이트아이오 최상단 호가 조회
        try:
            res = await client.get("https://api.gateio.ws/api/v4/spot/tickers")
            for item in res.json():
                symbol = item["currency_pair"]
                highest_bid = float(item.get("highest_bid", 0))
                if symbol.endswith("_USDT") and highest_bid > 0:
                    coin = symbol.replace("_USDT", "")
                    gate_sell_prices[coin] = highest_bid * usdt_krw
        except Exception as e:
            print("Gate.io Error:", e)

        # 6. 실질 차익 계산 (1.0% 이상만 추출)
        opportunities = []

        for coin, buy_price in bithumb_buy_prices.items():
            if buy_price <= 0 or coin == "USDT": continue

            target_exchanges = {}
            if coin in upbit_sell_prices: target_exchanges["업비트"] = upbit_sell_prices[coin]
            if coin in binance_sell_prices: target_exchanges["바이낸스"] = binance_sell_prices[coin]
            if coin in bybit_sell_prices: target_exchanges["바이비트"] = bybit_sell_prices[coin]
            if coin in gate_sell_prices: target_exchanges["게이트아이오"] = gate_sell_prices[coin]

            if target_exchanges:
                best_sell_ex = max(target_exchanges, key=target_exchanges.get)
                best_sell_price = target_exchanges[best_sell_ex]

                profit_rate = ((best_sell_price - buy_price) / buy_price) * 100

                if 1.0 <= profit_rate <= 25.0:
                    opportunities.append({
                        "symbol": coin,
                        "buy_price": buy_price,
                        "sell_ex": best_sell_ex,
                        "sell_price": best_sell_price,
                        "profit_rate": round(profit_rate, 2)
                    })

        opportunities.sort(key=lambda x: x["profit_rate"], reverse=True)

        return {
            "usdt_krw": round(usdt_krw, 2),
            "opportunities": opportunities
        }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await fetch_prices()
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(2)
        except Exception as e:
            print("WS Error:", e)
            break