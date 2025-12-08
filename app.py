from flask import Flask, request, jsonify
import logging
import time
import random

app = Flask(__name__)

# 금융권 스타일 로그 설정 (Loki가 좋아합니다)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

@app.route('/')
def home():
    return "<h1>🏦 NH AI Financial Chatbot v1.0</h1><p>Status: Healthy</p>"

@app.route('/chat', methods=['POST'])
def chat():
    # 1. 요청 받기
    data = request.json
    user_msg = data.get('message', '')
    
    # 2. 로그 남기기 (시나리오 5번: 로그 분석용)
    logging.info(f"User Request: {user_msg}")

    # 3. AI 연산 흉내내기 (시나리오 6번: CPU 부하 유발용)
    # 복잡한 계산을 하는 척 딜레이를 줍니다.
    time.sleep(random.uniform(0.1, 0.5))

    # 4. 응답 로직
    if "대출" in user_msg:
        logging.warning("Loan inquiry detected - Risk Check Required")
        return jsonify({"response": "대출 관련 상담은 신용점수 조회가 필요합니다."})
    elif "오류" in user_msg:
        logging.error("Model Inference Error: Unknown Token")
        return jsonify({"response": "죄송합니다. 처리 중 오류가 발생했습니다."}), 500
    
    return jsonify({"response": f"AI 모델 v1이 답변합니다: '{user_msg}'에 대한 안내입니다."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
