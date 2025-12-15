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

# --- [설정] 현재 버전 및 상태 ---
SYSTEM_VERSION = "v4.0 (Latest Security Patch)" # ⭐⭐ 배포할 새 버전 (v4.0) ⭐⭐
LAST_UPDATE = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
SYSTEM_STATUS = "Normal (Active)"
POD_NAME = os.getenv("HOSTNAME", "finbot-worker-node-unknown") # Pod 이름을 환경변수에서 가져오도록 수정

# --- [Prometheus 메트릭 정의] ---
# 애플리케이션 버전 정보를 담는 Gauge (버전 확인용)
APP_VERSION = Gauge('finbot_app_info', 'Application version and info', ['version', 'pod_name'])
# HTTP 요청 카운터
REQUEST_COUNT = Counter('finbot_http_requests_total', 'Total HTTP Requests', ['method', 'endpoint', 'status'])
# HTTP 요청 지연 시간 히스토그램
REQUEST_LATENCY = Histogram('finbot_http_request_duration_seconds', 'HTTP Request Latency', ['method', 'endpoint'])
# Prometheus Operator가 잘 스크랩할 수 있도록 service name과 namespace 정보를 레이블로 추가할 수도 있음.


# --- [디자인] 금융권 대시보드 스타일 HTML ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NH AI Platform - Model Ops Control</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background-color: #f4f6f9; font-family: 'Noto Sans KR', sans-serif; }
        .sidebar { background-color: #00305b; color: white; min-height: 100vh; padding: 20px; }
        .sidebar h4 { font-weight: bold; margin-bottom: 30px; letter-spacing: 1px; }
        .menu-item { padding: 10px; margin: 5px 0; border-radius: 5px; cursor: pointer; opacity: 0.8; }
        .menu-item:hover, .menu-item.active { background-color: #004c8c; opacity: 1; }
        .card-custom { border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-radius: 10px; }
        .status-dot { height: 12px; width: 12px; background-color: #28a745; border-radius: 50%; display: inline-block; margin-right: 5px; }
        .chat-box { height: 400px; overflow-y: auto; background-color: #ffffff; border: 1px solid #e9ecef; border-radius: 10px; padding: 20px; }
        .message { margin-bottom: 15px; padding: 10px 15px; border-radius: 15px; max-width: 80%; }
        .message.user { background-color: #0055a5; color: white; margin-left: auto; text-align: right; border-bottom-right-radius: 0; }
        .message.bot { background-color: #f1f3f5; color: #333; margin-right: auto; border-bottom-left-radius: 0; }
        .header-badge { background-color: #e3f2fd; color: #0d47a1; padding: 5px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <div class="col-md-2 sidebar d-none d-md-block">
                <h4><i class="fas fa-university"></i> NH AI Platform</h4>
                <div class="menu-item active"><i class="fas fa-tachometer-alt"></i> 대시보드</div>
                <div class="menu-item"><i class="fas fa-robot"></i> 모델 관리 (MLOps)</div>
                <div class="menu-item"><i class="fas fa-server"></i> 인프라 모니터링</div>
                <div class="menu-item"><i class="fas fa-shield-alt"></i> 보안/컴플라이언스</div>
                <div class="mt-5">
                    <small>System Info</small><br>
                    <strong>Kubernetes Cluster</strong><br>
                    <span class="text-success"><i class="fas fa-check-circle"></i> Connected</span>
                </div>
            </div>

            <div class="col-md-10 p-4">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h3><i class="fas fa-project-diagram"></i> 챗봇 모델 자동 배포 현황</h3>
                    <div>
                        <span class="header-badge me-2">Namespace: Default</span>
                        <span class="header-badge">Node: Worker-1</span>
                    </div>
                </div>

                <div class="row mb-4">
                    <div class="col-md-4">
                        <div class="card card-custom p-3 bg-white">
                            <h6 class="text-muted">Current Model Version</h6>
                            <h2 class="text-primary fw-bold">{{ version }}</h2>
                            <small class="text-muted"><i class="far fa-clock"></i> Updated: {{ last_update }}</small>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card card-custom p-3 bg-white">
                            <h6 class="text-muted">Pod Status</h6>
                            <h2><span class="status-dot"></span> {{ status }}</h2>
                            <small class="text-muted">ReplicaSet: 2/2 Running</small>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card card-custom p-3 bg-white">
                            <h6 class="text-muted">Pod Name (Host)</h6>
                            <h5>{{ pod_name }}</h5>
                            <small class="text-info">Auto-Scaling Enabled (HPA)</small>
                        </div>
                    </div>
                </div>

                <div class="row">
                    <div class="col-12">
                        <div class="card card-custom">
                            <div class="card-header bg-white fw-bold">
                                <i class="fas fa-comment-dots"></i> 실시간 챗봇 테스트 (Live Demo)
                            </div>
                            <div class="card-body">
                                <div id="chat-window" class="chat-box mb-3">
                                    <div class="message bot">
                                        안녕하세요! NH AI 금융 챗봇 <strong>{{ version }}</strong> 모델입니다.<br>
                                        무엇을 도와드릴까요? (예: 대출, 금리, 상품 안내)
                                    </div>
                                </div>
                                <div class="input-group">
                                    <input type="text" id="user-input" class="form-control" placeholder="메시지를 입력하세요..." onkeypress="if(event.keyCode==13) sendMessage()">
                                    <button class="btn btn-primary" onclick="sendMessage()"><i class="fas fa-paper-plane"></i> 전송</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function sendMessage() {
            var input = document.getElementById("user-input");
            var message = input.value;
            if (message.trim() === "") return;

            // 사용자 메시지 표시
            var chatWindow = document.getElementById("chat-window");
            chatWindow.innerHTML += `<div class='message user'>${message}</div>`;
            input.value = "";
            chatWindow.scrollTop = chatWindow.scrollHeight;

            // 서버로 전송 (API 호출)
            fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            })
            .then(response => response.json())
            .then(data => {
                // 봇 응답 표시
                chatWindow.innerHTML += `<div class='message bot'>${data.response}</div>`;
                chatWindow.scrollTop = chatWindow.scrollHeight;
            })
            .catch(error => {
                chatWindow.innerHTML += `<div class='message bot text-danger'>서버 연결 오류가 발생했습니다.</div>`;
            });
        }
    </script>
</body>
</html>
"""

# Prometheus 미들웨어 설정
@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    # API 요청 카운트 및 지연 시간 메트릭 수집
    latency = time.time() - request.start_time
    REQUEST_COUNT.labels(request.method, request.path, response.status_code).inc()
    REQUEST_LATENCY.labels(method=request.method, endpoint=request.path).observe(latency) # Histogram은 observe 메서드 사용
    return response

@app.route('/metrics') # ⭐⭐ Prometheus가 스크랩할 /metrics 엔드포인트 ⭐⭐
def metrics():
    # 애플리케이션 버전 정보를 Gauge에 설정
    # 각 Pod가 자신의 버전을 노출하도록 1을 설정. Pod가 여러개여도 version과 pod_name 레이블이 다르면 각각 트랙킹
    APP_VERSION.labels(version=SYSTEM_VERSION, pod_name=POD_NAME).set(1)
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/')
def home():
    # 템플릿에 현재 시스템 상태 변수 전달
    return render_template_string(HTML_TEMPLATE,
                                  version=SYSTEM_VERSION,
                                  last_update=LAST_UPDATE,
                                  status=SYSTEM_STATUS,
                                  pod_name=POD_NAME)

@app.route('/chat', methods=['POST'])
def chat():
    # --- [기존 로직 유지] ---
    data = request.json
    user_msg = data.get('message', '')

    logging.info(f"[User Query] {user_msg}")

    # AI 연산 시뮬레이션 (HPA 테스트용 부하)
    time.sleep(random.uniform(0.1, 0.3))

    # 응답 로직
    if "대출" in user_msg or "금리" in user_msg:
        logging.warning(f"Risk Check: {user_msg}")
        return jsonify({"response": "📋 <strong>[신용정보 조회 필요]</strong><br>고객님의 신용점수 조회 후 최적의 금리를 안내해 드릴 수 있습니다."})

    elif "오류" in user_msg:
        logging.error("Model Error Simulation")
        return jsonify({"response": "⚠️ <strong>시스템 오류</strong><br>관리자에게 알림이 전송되었습니다."}), 500

    else:
        return jsonify({"response": f"🤖 <strong>[AI v4.0 답변]</strong><br>'{user_msg}'에 대한 안내를 도와드리겠습니다."}) # ⭐⭐ v4.0 답변으로 변경 ⭐⭐

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
