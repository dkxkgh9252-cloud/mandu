<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>빗썸 출발 전체 코인 실시간 차익 스캐너</title>
    <style>
        body { background-color: #121212; color: #ffffff; font-family: 'Pretendard', sans-serif; margin: 0; padding: 20px; }
        .header { text-align: center; margin-bottom: 20px; }
        .header h1 { color: #f39c12; margin: 0 0 8px 0; font-size: 1.8rem; }
        .sub-info { color: #888; font-size: 0.85rem; }
        .status-badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; margin-left: 8px; }
        .status-online { background-color: #2ecc71; color: #000; }
        .status-offline { background-color: #e74c3c; color: #fff; }
        .grid-container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background-color: #1a1a1a; border-radius: 10px; padding: 15px; border: 1px solid #2d2d2d; }
        .card-header { font-size: 1.05rem; font-weight: bold; padding-bottom: 10px; border-bottom: 1px solid #333; display: flex; justify-content: space-between; margin-bottom: 10px; }
        .high-title { color: #ff9f43; }
        .normal-title { color: #2ecc71; }
        .table-container { max-height: 78vh; overflow-y: auto; }
        table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.85rem; }
        th { position: sticky; top: 0; background-color: #222; padding: 8px; color: #aaa; font-weight: normal; font-size: 0.8rem; }
        td { padding: 8px; border-bottom: 1px solid #262626; }
        .badge { padding: 2px 5px; border-radius: 3px; font-size: 0.72rem; font-weight: bold; background-color: #2b3a4a; color: #70a1ff; }
        .profit-high { color: #ff9f43; font-weight: bold; font-size: 0.95rem; }
        .profit-normal { color: #2ecc71; font-weight: bold; font-size: 0.95rem; }
    </style>
</head>
<body>

    <div class="header">
        <h1>🚀 빗썸 출발 전체 코인 차익 스캐너 <span id="conn-status" class="status-badge status-offline">연결 중...</span></h1>
        <div class="sub-info">기준 USDT 가격 (빗썸): <span id="usdt-rate" style="color:#f1c40f; font-weight:bold;">-</span> KRW | 필터: 빗썸 출금 가능 & 1.0% 이상</div>
    </div>

    <div class="grid-container">
        <!-- 1. 고수익 구간 (1.5% 이상) -->
        <div class="card">
            <div class="card-header high-title">
                <span>🔥 고수익 구간 (1.5% 이상)</span>
                <span id="high-count">0개</span>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr><th>코인</th><th>빗썸 (매수 1호가)</th><th>최고가 매도처</th><th>기대 수익률</th></tr>
                    </thead>
                    <tbody id="high-list"></tbody>
                </table>
            </div>
        </div>

        <!-- 2. 일반 구간 (1.0% ~ 1.5% 미만) -->
        <div class="card">
            <div class="card-header normal-title">
                <span>⚡ 일반 구간 (1.0% ~ 1.5% 미만)</span>
                <span id="normal-count">0개</span>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr><th>코인</th><th>빗썸 (매수 1호가)</th><th>최고가 매도처</th><th>기대 수익률</th></tr>
                    </thead>
                    <tbody id="normal-list"></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        let socket;

        function connectWebSocket() {
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            socket = new WebSocket(`${wsProtocol}//${window.location.host}/ws`);

            const statusBadge = document.getElementById('conn-status');

            socket.onopen = function() {
                statusBadge.innerText = '실시간 연결됨';
                statusBadge.className = 'status-badge status-online';
            };

            socket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                document.getElementById('usdt-rate').innerText = `${data.usdt_krw}`;
                renderRows(data.high, 'high-list', 'high-count', true);
                renderRows(data.normal, 'normal-list', 'normal-count', false);
            };

            socket.onclose = function() {
                statusBadge.innerText = '재연결 시도 중...';
                statusBadge.className = 'status-badge status-offline';
                // 연결이 끊기면 1초 후 자동 재연결
                setTimeout(connectWebSocket, 1000);
            };

            socket.onerror = function() {
                socket.close();
            };
        }

        function renderRows(list, targetId, countId, isHigh) {
            const tbody = document.getElementById(targetId);
            document.getElementById(countId).innerText = `${list.length}개`;
            
            if (list.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#555;">해당 구간 코인 없음</td></tr>';
                return;
            }

            tbody.innerHTML = list.map(item => `
                <tr>
                    <td><strong>${item.symbol}</strong></td>
                    <td>${item.bithumb_price}</td>
                    <td><span class="badge">${item.sell_ex}</span><br><small style="color:#aaa;">${item.sell_price}</small></td>
                    <td class="${isHigh ? 'profit-high' : 'profit-normal'}">+${item.profit}%</td>
                </tr>
            `).join('');
        }

        // 웹소켓 연결 실행
        connectWebSocket();
    </script>
</body>
</html>
