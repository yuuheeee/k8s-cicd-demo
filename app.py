from flask import Flask, request, jsonify, render_template_string
import logging
import time
import random
import os
import datetime

# Prometheus 클라이언트 라이브러리 임포트
from prometheus_client import generate_latest, Gauge, Counter, Histogram

app = Flask(__name__)

# 금융권 로그 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# --- [설정] 버전 정보 (롤링 업데이트 확인용) ---
SYSTEM_VERSION = "v4.0 (Latest Security Patch)" # ⭐ 업데이트할 버전
LAST_UPDATE = datetime.datetime.now().strftime("%Y-%m-%d")

# --- [Prometheus 메트릭] ---
APP_VERSION = Gauge('finbot_app_info', 'Application version', ['version'])
REQUEST_COUNT = Counter('finbot_http_requests_total', 'Total HTTP Requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('finbot_http_request_duration_seconds', 'HTTP Request Latency', ['method', 'endpoint'])

# --- [디자인] 고객용 금융 상담 앱 스타일 ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NH AI Financial Service</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background-color: #f0f2f5; font-family: 'Noto Sans KR', sans-serif; }
        .sidebar { background-color: #004c8c; color: white; min-height: 100vh; padding: 25px; }
        .sidebar h4 { font-weight: bold; margin-bottom: 40px; font-size: 1.3rem; }
        .menu-item { padding: 12px 15px; margin: 8px 0; border-radius: 10px; cursor: pointer; transition: all 0.3s; font-size: 1.05rem; }
        .menu-item:hover, .menu-item.active { background-color: #00305b; font-weight: bold; transform: translateX(5px); }
        .menu-item i { margin-right: 10px; width: 25px; text-align: center; }
        .main-content { padding: 40px; }
        .welcome-card { background: linear-gradient(135deg, #005aa7, #fffde4); color: white; border: none; border-radius: 15px; padding: 30px; margin-bottom: 30px; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
        .welcome-text h2 { font-weight: 800; text-shadow: 1px 1px 3px rgba(0,0,0,0.2); }
        .chat-card { border: none; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); overflow: hidden; background: white; }
        .chat-header { background-color: #ffffff; border-bottom: 1px solid #eee; padding: 20px; font-weight: bold; color: #333; display: flex; justify-content: space-between; align-items: center; }
        .chat-box { height: 450px; overflow-y: auto; background-color: #f8f9fa; padding: 25px; }
        .message { margin-bottom: 20px; padding: 12px 18px; border-radius: 18px; max-width: 75%; font-size: 0.95rem; line-height: 1.5; position: relative; }
        .message.user { background-color: #0d6efd; color: white; margin-left: auto; border-bottom-right-radius: 4px; box-shadow: 0 2px 5px rgba(13, 110, 253, 0.2); }
        .message.bot { background-color: #ffffff; color: #444; margin-right: auto; border-bottom-left-radius: 4px; border: 1px solid #e9ecef; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        .bot-avatar { width: 35px; height: 35px; background-color: #ffc107; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 10px; color: white; }
        .msg-container { display: flex; align-items: flex-end; }
        .input-area { padding: 20px; background-color: white; border-top: 1px solid #f0f0f0; }
        .form-control { border-radius: 30px; padding: 12px 20px; background-color: #f8f9fa; border: 1px solid #e0e0e0; }
        .form-control:focus { box-shadow: none; border-color: #0d6efd; background-color: white; }
        .btn-send { border-radius: 50%; width: 45px; height: 45px; padding: 0; display: flex; align-items: center; justify-content: center; margin-left: 10px; box-shadow: 0 3px 6px rgba(0,0,0,0.1); }
        .version-badge { font-size: 0.75rem; background-color: rgba(0,0,0,0.1); padding: 5px 10px; border-radius: 20px; color: #666; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <div class="col-md-2 sidebar d-none d-md-block">
                <h4><i class="fas fa-university"></i> NH Financial</h4>
                <div class="menu-item active"><i class="fas fa-headset"></i> AI 스마트 상담</div>
                <div class="menu-item"><i class="fas fa-wallet"></i> 내 자산 현황</div>
                <div class="menu-item"><i class="fas fa-exchange-alt"></i> 이체/송금</div>
                <div class="menu-item"><i class="fas fa-hand-holding-usd"></i> 대출 상품몰</div>
                <div class="menu-item"><i class="fas fa-cog"></i> 설정</div>
                <div class="mt-5 pt-5 text-white-50 text-center"><small>고객센터 1588-0000</small></div>
            </div>
            <div class="col-md-10 main-content">
                <div class="row"><div class="col-12"><div class="welcome-card welcome-text"><h2>안녕하세요, 김농협 고객님! 👋</h2><p class="mb-0 op-7">무엇을 도와드릴까요? AI 금융 비서가 24시간 대기중입니다.</p></div></div></div>
                <div class="row justify-content-center"><div class="col-lg-10"><div class="chat-card">
                    <div class="chat-header"><div><i class="fas fa-robot text-primary me-2"></i> 스마트 금융 비서</div><div class="version-badge">System Version: {{ version }}</div></div>
                    <div id="chat-window" class="chat-box">
                        <div class="text-center mb-4 text-muted"><small>{{ last_update }} 기준 금리 정보가 업데이트 되었습니다.</small></div>
                        <div class="msg-container"><div class="bot-avatar"><i class="fas fa-robot"></i></div><div class="message bot">반갑습니다! <strong>{{ version }}</strong> AI 비서입니다.<br>예금, 대출, 환율 등 궁금한 점을 물어보세요.</div></div>
                    </div>
                    <div class="input-area"><div class="d-flex"><input type="text" id="user-input" class="form-control" placeholder="메시지를 입력하세요..." onkeypress="if(event.keyCode==13) sendMessage()"><button class="btn btn-primary btn-send" onclick="sendMessage()"><i class="fas fa-paper-plane"></i></button></div></div>
                </div></div></div>
            </div>
        </div>
    </div>
    <script>
        function sendMessage() {
            var input = document.getElementById("user-input");
            var message = input.value;
            if (message.trim() === "") return;
            var chatWindow = document.getElementById("chat-window");
            chatWindow.innerHTML += `<div class='msg-container justify-content-end'><div class='message user'>${message}</div></div>`;
            input.value = "";
            chatWindow.scrollTop = chatWindow.scrollHeight;
            fetch('/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: message }) })
            .then(response => response.json())
            .then(data => { setTimeout(() => { chatWindow.innerHTML += `<div class='msg-container'><div class='bot-avatar'><i class='fas fa-robot'></i></div><div class='message bot'>${data.response}</div></div>`; chatWindow.scrollTop = chatWindow.scrollHeight; }, 300); })
            .catch(error => { chatWindow.innerHTML += `<div class='text-center text-danger my-3'><small>연결 상태가 불안정합니다.</small></div>`; });
        }
    </script>
</body>
</html>
"""

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    latency = time.time() - request.start_time
    REQUEST_COUNT.labels(request.method, request.path, response.status_code).inc()
    REQUEST_LATENCY.labels(method=request.method, endpoint=request.path).observe(latency)
    return response

@app.route('/metrics')
def metrics():
    APP_VERSION.labels(version=SYSTEM_VERSION).set(1)
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, version=SYSTEM_VERSION, last_update=LAST_UPDATE)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_msg = data.get('message', '')
    logging.info(f"[Customer Query] {user_msg}")
    time.sleep(random.uniform(0.1, 0.3))
    if "대출" in user_msg or "금리" in user_msg:
        return jsonify({"response": "📋 <strong>[신용정보 조회]</strong><br>고객님의 우대 금리를 조회하고 있습니다. 잠시만 기다려주세요."})
    elif "오류" in user_msg:
        return jsonify({"response": "⚠️ <strong>시스템 알림</strong><br>일시적인 오류입니다."}), 500
    else:
        return jsonify({"response": f"🤖 <strong>[AI v4.0]</strong><br>'{user_msg}'에 대해 안내해 드리겠습니다."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
