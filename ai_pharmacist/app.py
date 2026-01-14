from flask import Flask, request, jsonify, render_template
from openai import OpenAI
import sqlite3
import os
import time
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

app = Flask(__name__)

# --- [기존 기능] DB 저장 & 도배 방지 ---
user_timestamps = {}

def is_spam(user_ip):
    current_time = time.time()
    if user_ip not in user_timestamps:
        user_timestamps[user_ip] = []
    timestamps = user_timestamps[user_ip]
    user_timestamps[user_ip] = [t for t in timestamps if current_time - t < 60]
    if len(user_timestamps[user_ip]) >= 5:
        return True
    user_timestamps[user_ip].append(current_time)
    return False

def save_to_db(sender, message):
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO chats (sender, message) VALUES (?, ?)', (sender, message))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ DB 저장 오류: {e}")

# --- [기존 기능] 웹사이트용 ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask')
def ask_ai():
    # ... (기존 웹 채팅 코드는 그대로 둠)
    user_query = request.args.get('q')
    if not user_query: return "질문 입력 필요"
    
    save_to_db("웹_환자", user_query) # 웹에서 온 건 '웹_환자'로 기록
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "친절한 약사입니다. 3줄 요약 답변."},
                {"role": "user", "content": user_query}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return str(e)

# --- [★NEW★] 카카오톡 전용 창구 ---
@app.route('/kakao', methods=['POST'])
def kakao_chatbot():
    # 1. 카카오톡이 보내준 데이터 받기 (JSON)
    body = request.get_json()
    
    try:
        # 2. 사용자가 카톡으로 보낸 문장(utterance) 꺼내기
        user_query = body['userRequest']['utterance']
        user_id = body['userRequest']['user']['id'] # 카톡이 주는 진짜 ID
        
        # 3. DB에 저장
        save_to_db(f"카톡_{user_id[:5]}", user_query)

        # 4. AI에게 물어보기
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "너는 카카오톡 챗봇 약사야. 친절하게 3줄 이내로 답변해."},
                {"role": "user", "content": user_query}
            ]
        )
        ai_response = completion.choices[0].message.content
        
        # 5. 답변도 DB 저장
        save_to_db("AI약사", ai_response)

        # 6. ★중요★ 카카오톡이 알아듣는 포맷(JSON)으로 포장해서 보내기
        response_body = {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": ai_response
                        }
                    }
                ]
            }
        }
        return jsonify(response_body)

    except Exception as e:
        # 에러 나면 카톡한테 "잠시 오류가.." 라고 보냄
        return jsonify({
            "version": "2.0",
            "template": {
                "outputs": [{"simpleText": {"text": "죄송합니다. 서버 처리 중 오류가 발생했습니다."}}]
            }
        })

if __name__ == '__main__':
    app.run(debug=True)
