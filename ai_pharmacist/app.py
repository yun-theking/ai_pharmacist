from flask import Flask, request, render_template
from openai import OpenAI
import sqlite3
import os
from dotenv import load_dotenv

# 1. 보안 설정: 금고(.env)에서 키 꺼내오기
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# 키가 제대로 있는지 검사 (없으면 에러 메시지 띄움)
if not api_key:
    print("🚨 오류: .env 파일을 찾을 수 없거나 키가 없습니다!")

client = OpenAI(api_key=api_key)

app = Flask(__name__)

# --- [기능 1] DB에 기록하는 함수 (서기) ---
def save_to_db(sender, message):
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO chats (sender, message) VALUES (?, ?)', (sender, message))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ DB 저장 오류: {e}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask')
def ask_ai():
    user_query = request.args.get('q')
    if not user_query:
        return "질문을 입력해주세요."

    # 1. 사용자 질문 저장
    save_to_db("환자", user_query)

    try:
        # 2. AI에게 질문
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "너는 친절한 약사야. 환자에게 공감해주고 3줄 이내로 답변해줘."},
                {"role": "user", "content": user_query}
            ]
        )
        ai_response = completion.choices[0].message.content

        # 3. AI 답변 저장
        save_to_db("AI약사", ai_response)
        
        return ai_response

    except Exception as e:
        return f"오류 발생: {str(e)}"

# --- [기능 2] 관리자용: 상담 내역 몰래보기 ---
@app.route('/history')
def show_history():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        # 최신순(내림차순)으로 가져오기
        cursor.execute('SELECT sender, message, timestamp FROM chats ORDER BY id DESC')
        rows = cursor.fetchall()
        conn.close()

        # 간단한 표(HTML)로 보여주기
        html = """
        <style>
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            tr:nth-child(even) { background-color: #f9f9f9; }
        </style>
        <h1>📊 상담 기록 대장 (관리자용)</h1>
        <table>
            <tr><th>시간</th><th>발화자</th><th>내용</th></tr>
        """
        for row in rows:
            html += f"<tr><td>{row[2]}</td><td>{row[0]}</td><td>{row[1]}</td></tr>"
        html += "</table>"
        return html
    except Exception as e:
        return f"DB 읽기 오류: {e}"

if __name__ == '__main__':
    app.run(debug=True)