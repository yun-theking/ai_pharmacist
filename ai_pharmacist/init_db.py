import sqlite3

# 1. 장부(파일)을 엽니다. 없으면 새로 만듭니다.
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# 2. 'chats'라는 이름의 표(Table)를 만듭니다.
# 컬럼: 번호(id), 누가(sender), 내용(message), 언제(timestamp)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# 3. 저장하고 닫습니다.
conn.commit()
conn.close()

print("✅ 장부(DB) 생성 완료! 'database.db' 파일이 생겼을 겁니다.")