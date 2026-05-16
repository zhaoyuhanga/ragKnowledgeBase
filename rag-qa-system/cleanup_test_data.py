import os
os.chdir('d:/work/agentV1/rag-qa-system')

from app.config import settings
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

url = settings.mysql_url + "?charset=utf8mb4"
engine = create_engine(url)
Session = sessionmaker(bind=engine)
db = Session()

try:
    # 清理测试数据（问题长度小于5的记录）
    result = db.execute(text("DELETE FROM qa_logs WHERE LENGTH(question) < 5"))
    db.commit()
    print(f"Deleted {result.rowcount} short test records")

    # 查看剩余记录
    result = db.execute(text("SELECT id, question, LENGTH(question) as qlen FROM qa_logs ORDER BY id DESC LIMIT 10"))
    print("\n=== Remaining QA Logs ===")
    for row in result:
        q = row[1] if row[1] else '(empty)'
        print(f"ID={row[0]}, Question=\"{q}\", Length={row[2]}")

    # 检查文档状态
    print("\n=== Document Status ===")
    result = db.execute(text("SELECT id, filename, status, chunk_count FROM documents ORDER BY id DESC LIMIT 10"))
    for row in result:
        print(f"ID={row[0]}, filename=\"{row[1]}\", status={row[2]}, chunks={row[3]}")

finally:
    db.close()
