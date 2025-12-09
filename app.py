from flask import Flask, request, jsonify
import logging
import time
import random
import os

app = Flask(__name__)

# 금융권 스타일 로그 포맷 설정 (Loki 분석용)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

@app.route('/')
def home():
    # 웹 브라우저 접속 시 보여줄 화면
    return """
    <div style="text-align: center; margin-top: 50px; font-family: Arial;">
        <h1>🚀 NH AI Financial Chatbot v2.0 (Upgrade)</h1> <p style="color: blue; font-weight: bold;">Status: System Healthy (Active)</p> <p>새로운 모델이 적용되었습니다.</p>
    </div>
    """

@app.route('/chat', methods=['POST'])
def chat():
    # 1. 사용자 요청 받기
    data = request.json
    user_msg = data.get('message', '')
    
    # 2. 로그 기록 (시나리오 5: 장애 분석용)
    logging.info(f"[User Query] {user_msg}")

    # 3. AI 연산 시뮬레이션 (시나리오 6: HPA 오토스케일링용)
    # CPU 부하를 주는 척 딜레이를 줍니다.
    time.sleep(random.uniform(0.1, 0.3))

    # 4. 답변 로직 (금융 시나리오)
    if "대출" in user_msg or "금리" in user_msg:
        logging.warning(f"Risk Assessment Required: Loan inquiry detected - '{user_msg}'")
        return jsonify({"response": "대출/금리 상담은 신용점수 조회 동의가 필요합니다. 진행하시겠습니까?"})
    
    elif "오류" in user_msg or "error" in user_msg:
        logging.error("Critical Model Failure: Unknown Token Exception")
        return jsonify({"response": "시스템 오류가 발생했습니다. 관리자에게 문의하세요."}), 500
    
    else:
        return jsonify({"response": f"AI 챗봇이 답변합니다: '{user_msg}'에 대한 안내를 도와드리겠습니다."})

if __name__ == '__main__':
    # 중요: 포트를 8080으로 엽니다.
    app.run(host='0.0.0.0', port=8080)
