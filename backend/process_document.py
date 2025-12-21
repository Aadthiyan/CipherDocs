"""
Manually process a document
"""
import sys
import asyncio
from app.db.database import get_db
from app.models.database import Document
from app.processing.sync_processor import process_document_sync

async def process_doc(document_id: str):
    """Process a document manually"""
    db = next(get_db())
    
    try:
        # Find document
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            print(f"❌ Document not found: {document_id}")
            return
        
        print(f"✅ Found document: {doc.filename}")
        print(f"   Status: {doc.status}")
        print(f"   Tenant: {doc.tenant_id}")
        print()
        print("🔄 Starting document processing...")
        print()
        
        # Process document
        result = await process_document_sync(doc.id, db)
        
        print()
        print(f"✅ Processing complete!")
        print(f"   Chunks created: {result.get('chunks_created', 0)}")
        print(f"   Vectors indexed: {result.get('vectors_indexed', 0)}")
        print(f"   Status: {result.get('status', 'unknown')}")
        
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_document.py <document_id>")
        sys.exit(1)
    
    document_id = sys.argv[1]
    asyncio.run(process_doc(document_id))
