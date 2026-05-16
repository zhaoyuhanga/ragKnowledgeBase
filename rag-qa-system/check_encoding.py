import os
os.chdir('d:/work/agentV1/rag-qa-system')

from app.config import settings
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 添加字符集参数
url = settings.mysql_url + "?charset=utf8mb4"
engine = create_engine(url)
Session = sessionmaker(bind=engine)
db = Session()

try:
    # 检查数据库字符集
    result = db.execute(text("SHOW VARIABLES LIKE 'character_set%'"))
    print("=== MySQL Character Set ===")
    for row in result:
        print(f"  {row[0]}: {row[1]}")
    print()

    # 检查表字符集
    result = db.execute(text("SHOW FULL COLUMNS FROM qa_logs WHERE Field = 'question'"))
    print("=== Question Column ===")
    for row in result:
        print(f"  Collation: {row[2]}")
    print()

    # 尝试读取原始字节
    result = db.execute(text("SELECT id, question, LENGTH(question), HEX(question) FROM qa_logs"))
    print("=== Raw Data ===")
    for row in result:
        print(f"ID={row[0]}, Length={row[2]}, Hex={row[3][:50]}...")

finally:
    db.close()
