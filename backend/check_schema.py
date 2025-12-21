from app.db.database import get_db
from sqlalchemy import inspect

db = next(get_db())
inspector = inspect(db.bind)
columns = inspector.get_columns('document_chunks')

print("document_chunks columns:")
for col in columns:
    print(f"  {col['name']}: {col['type']}")
