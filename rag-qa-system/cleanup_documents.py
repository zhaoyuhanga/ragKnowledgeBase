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
    # 删除文件名包含乱码的文档记录
    print("=== Checking documents with corrupted filenames ===")
    result = db.execute(text("SELECT id, filename FROM documents"))
    corrupted_ids = []
    for row in result:
        print(f"ID={row[0]}, filename=\"{row[1]}\"")
        # 检查是否包含替换字符
        if '\ufffd' in row[1] or '?' in row[1]:
            corrupted_ids.append(row[0])

    if corrupted_ids:
        print(f"\nDeleting corrupted documents: {corrupted_ids}")
        db.execute(text(f"DELETE FROM document_chunks WHERE document_id IN ({','.join(map(str, corrupted_ids))})"))
        db.execute(text(f"DELETE FROM documents WHERE id IN ({','.join(map(str, corrupted_ids))})"))
        db.commit()
        print("Deleted successfully")
    else:
        print("\nNo corrupted filenames found")

    # 查看剩余文档
    print("\n=== Remaining documents ===")
    result = db.execute(text("SELECT id, filename, status, chunk_count FROM documents"))
    for row in result:
        print(f"ID={row[0]}, filename=\"{row[1]}\", status={row[2]}, chunks={row[3]}")

finally:
    db.close()
