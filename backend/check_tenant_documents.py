"""
Check tenant documents and their processing status
"""
import sys
from app.db.database import get_db
from app.models.database import Tenant, User, Document, DocumentChunk

def check_tenant_docs(tenant_id: str):
    """Check documents and chunks for a tenant"""
    db = next(get_db())
    
    try:
        # Find tenant
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            print(f"❌ Tenant not found: {tenant_id}")
            return
        
        print(f"✅ Found tenant: {tenant.name} (ID: {tenant.id})")
        print()
        
        # Get all documents
        documents = db.query(Document).filter(Document.tenant_id == tenant.id).all()
        print(f"📄 Total documents: {len(documents)}")
        print()
        
        if not documents:
            print("❌ No documents found for this tenant!")
            print("   Upload a document first before searching.")
            return
        
        # Check each document
        for doc in documents:
            print(f"📄 Document: {doc.filename}")
            print(f"   ID: {doc.id}")
            print(f"   Status: {doc.status}")
            print(f"   Updated: {doc.updated_at}")
            
            # Check chunks
            chunks = db.query(DocumentChunk).filter(DocumentChunk.doc_id == doc.id).all()
            print(f"   Chunks: {len(chunks)}")
            
            if chunks:
                embedded_chunks = [c for c in chunks if c.encrypted_embedding is not None]
                print(f"   Embedded chunks: {len(embedded_chunks)}/{len(chunks)}")
                
                if embedded_chunks:
                    print(f"   ✅ Document has embedded chunks - should be searchable")
                else:
                    print(f"   ⚠️ Chunks exist but no embeddings - processing may have failed")
            else:
                print(f"   ❌ No chunks found - document processing incomplete")
            
            print()
    
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_tenant_documents.py <tenant_id>")
        sys.exit(1)
    
    tenant_id = sys.argv[1]
    check_tenant_docs(tenant_id)
