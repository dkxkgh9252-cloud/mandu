<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>거래소별 빗썸 차익 스캐너</title>
    <style>
        body { background-color: #121212; color: #ffffff; font-family: 'Pretendard', sans-serif; margin: 0; padding: 15px; }
        .header { text-align: center; margin-bottom: 15px; }
        .header h1 { color: #f39c12; margin: 0 0 5px 0; font-size: 1.6rem; }
        .sub-info { color: #888; font-size: 0.85rem; }
        .status-badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; margin-left: 8px; }
        .status-online { background-color: #2ecc71; color: #000; }
        .status-offline { background-color: #e74c3c; color: #fff; }
        
        /* 다중 그리드 레이아웃 (거래소별 칸 나누기) */
        .grid-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 15px; }
        .card { background-color: #1a1a1a; border-radius: 10px; padding: 12px; border: 1px solid #2d2d2d; }
        .card-header { font-size: 1rem; font-weight: bold; padding-bottom: 8px; border-bottom: 1px solid #333; display: flex; justify-content: space-between; margin-bottom: 8px; color: #3498db; }
        .table-container { max-height: 38vh; overflow-y: auto; }
        table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.8rem; }
        th { position: sticky; top: 0; background-color: #222; padding: 6px; color: #aaa; font-weight: normal; }
        td { padding: 6px; border-bottom: 1px solid #262626; }
        .profit-pos { color: #2ecc71; font-weight: bold; }
    </style>
</head>
<body>

    <div class="header">
        <h1>🚀 거래소별 빗썸 출발 차익 스캐너 <span id="conn-status" class="status-badge status-offline">연결 중...</span></h1>
        <div class="sub-info">기준 USDT 가격 (빗썸): <span id="usdt-rate" style="color:#f1c40f; font-weight:bold;">-</span> KRW | 필터: 빗썸 출금 가능 & 1.0% 이상</div>
    </div>

    <div class="grid-container" id="exchange-grid">
        <!-- 동적으로 거래소별 카드가 생성됩니다 -->
    </div>

    <script>
        let socket;
        const exchanges = ['바이낸스', 'OKX', '바이비트', '비트겟', '게이트아이오', '업비트'];

        function initGrid() {
            const grid = document.getElementById('exchange-grid');
            grid.innerHTML = exchanges.map(ex => `
                <div class="card">
                    <div class="card-header">
                        <span>📊 ${ex} 비교</span>
                        <span id="count-${ex}">0개</span>
                    </div>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr><th>코인</th><th>빗썸가</th><th>매도가</th><th>수익률</th></tr>
                            </thead>
                            <tbody id="list-${ex}">
                                <tr><td colspan="4" style="text-align:center; color:#555;">데이터 수신 대기 중...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            `).join('');
        }

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
                document.getElementById('usdt-rate').innerText = data.usdt_krw;

                // 거래소별 데이터 분류
                let grouped = {};
                exchanges.forEach(ex => grouped[ex] = []);

                // 서버에서 온 데이터(high + normal 통합)를 거래소별로 분류
                const allItems = [...(data.high || []), ...(data.normal || [])];
                allItems.forEach(item => {
                    if (grouped[item.sell_ex]) {
                        grouped[item.sell_ex].push(item);
                    }
                });

                // 각 카드별 렌더링
                exchanges.forEach(ex => {
                    renderRows(grouped[ex], `list-${ex}`, `count-${ex}`);
                });
            };

            socket.onclose = function() {
                statusBadge.innerText = '재연결 시도 중...';
                statusBadge.className = 'status-badge status-offline';
                setTimeout(connectWebSocket, 1000);
            };
        }

        function renderRows(list, targetId, countId) {
            const tbody = document.getElementById(targetId);
            document.getElementById(countId).innerText = `${list.length}개`;
            
            if (list.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#555;">조건 충족 코인 없음</td></tr>';
                return;
            }

            // 수익률 높은 순으로 정렬
            list.sort((a, b) => b.profit - a.profit);

            tbody.innerHTML = list.map(item => `
                <tr>
                    <td><strong>${item.symbol}</strong></td>
                    <td>${item.bithumb_price}</td>
                    <td>${item.sell_price}</td>
                    <td class="profit-pos">+${item.profit}%</td>
                </tr>
            `).join('');
        }

        initGrid();
        connectWebSocket();
    </script>
</body>
</html>
