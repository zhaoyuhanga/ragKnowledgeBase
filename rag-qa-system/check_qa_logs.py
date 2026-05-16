import os
os.chdir('d:/work/agentV1/rag-qa-system')

from app.core.database import get_db
from app.models.document import QALog
from app.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.mysql_url)
Session = sessionmaker(bind=engine)
db = Session()

try:
    total = db.query(QALog).count()
    print(f'Total QA logs: {total}')
    print()

    logs = db.query(QALog).order_by(QALog.id.desc()).limit(20).all()
    for log in logs:
        q = log.question[:100] if log.question else '(empty)'
        a_len = len(log.answer) if log.answer else 0
        print(f'ID={log.id}')
        print(f'  Question: "{q}"')
        print(f'  Answer length: {a_len}')
        print(f'  Created: {log.created_at}')
        print()
finally:
    db.close()
