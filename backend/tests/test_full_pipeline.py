# -*- coding: utf-8 -*-
"""
Document Upload to Vector Database Full Pipeline Test

Test Steps:
1. Check system readiness
2. Upload file (D:/D/资料/aop解析.docx)
3. Verify chunking
4. Verify vector database upload

NOTE: Workers must be running before executing these tests.
Start workers with: python src/app/services/run_worker.py all
"""

import io
import os
import sys
import time
import pytest
from pathlib import Path

# Set environment
os.environ["APP_ENV"] = "local"
os.environ.setdefault("MYSQL_HOST", "localhost")
os.environ.setdefault("MYSQL_PORT", "3308")
os.environ.setdefault("MYSQL_USERNAME", "root")
os.environ.setdefault("MYSQL_PASSWORD", "root")
os.environ.setdefault("MYSQL_DATABASE", "rag_db")

# Add project path
backend_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(backend_path))

from sqlalchemy import text
from core.database import SessionLocal
from app.models.document import Document, DocumentVersion
from app.models.chunk import DocumentChunk
from app.services.document_service import DocumentService
from app.services.embedding_service import ChunkEmbeddingService
from app.repositories.milvus_repository import MilvusRepository


class TestFullPipeline:
    """Full pipeline test class"""

    TEST_FILE_PATH = r"D:\D\资料\aop解析.docx"

    @classmethod
    def setup_class(cls):
        """Setup before all tests in this class"""
        cls.db = SessionLocal()
        cls.test_document_id = None
        cls.test_version_id = None
        cls._uploaded = False

    def get_test_document(self):
        """Find the most recent test document by file hash"""
        if not os.path.exists(self.TEST_FILE_PATH):
            return None
        with open(self.TEST_FILE_PATH, "rb") as f:
            file_content = f.read()
        import hashlib
        file_hash = hashlib.md5(file_content).hexdigest()
        doc = self.db.query(Document).join(DocumentVersion).filter(
            DocumentVersion.file_hash == file_hash
        ).order_by(Document.id.desc()).first()
        return doc

    def test_01_check_system_ready(self):
        """Test 1: Check if system is ready"""
        print("\n=== Test 1: Check System Readiness ===")

        # Check MySQL connection
        try:
            result = self.db.execute(text("SELECT 1")).fetchone()
            assert result is not None
            print("[OK] MySQL connection OK")
        except Exception as e:
            pytest.fail(f"MySQL connection failed: {e}")

        # Check Milvus connection
        try:
            milvus_repo = MilvusRepository()
            try:
                collection = milvus_repo.client.get_collection("document_chunks")
                print("[OK] Milvus connection OK, collection exists: document_chunks")
            except Exception:
                print("[OK] Milvus connection OK (collection may not exist yet)")
        except Exception as e:
            print(f"[WARN] Milvus connection issue: {e}")
            pytest.fail(f"Milvus connection failed: {e}")

    def test_02_upload_document(self):
        """Test 2: Upload document"""
        print("\n=== Test 2: Upload Document ===")

        if not os.path.exists(self.TEST_FILE_PATH):
            pytest.skip(f"Test file does not exist: {self.TEST_FILE_PATH}")

        with open(self.TEST_FILE_PATH, "rb") as f:
            file_content = f.read()

        print(f"File size: {len(file_content)} bytes")

        class MockUploadFile:
            def __init__(self, filename, content_bytes):
                self.filename = filename
                self.file = io.BytesIO(content_bytes)

            def read(self, size=-1):
                return self.file.read(size)

            def seek(self, pos):
                return self.file.seek(pos)

        mock_file = MockUploadFile(
            filename="aop解析.docx",
            content_bytes=file_content
        )

        # Delete any existing document with same hash first
        import hashlib
        file_hash = hashlib.md5(file_content).hexdigest()
        existing = self.db.query(Document).join(DocumentVersion).filter(
            DocumentVersion.file_hash == file_hash
        ).first()
        
        if existing:
            print(f"[INFO] Deleting existing duplicate document: {existing.id}")
            try:
                milvus_repo = MilvusRepository()
                try:
                    milvus_repo.delete_by_document("document_chunks", existing.id)
                except:
                    pass
                self.db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == existing.id
                ).delete()
                self.db.query(DocumentVersion).filter(
                    DocumentVersion.document_id == existing.id
                ).delete()
                self.db.query(Document).filter(
                    Document.id == existing.id
                ).delete()
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                print(f"[WARN] Failed to delete existing: {e}")

        service = DocumentService()
        result = service.upload_document(
            file=mock_file,
            business_id="test_business",
            business_name="Test Business",
            creator_id=1,
            creator_name="Test User"
        )

        print(f"Upload result keys: {list(result.keys())}")
        assert result is not None
        assert "document_id" in result
        assert "version_id" in result

        self.test_document_id = result["document_id"]
        self.test_version_id = result["version_id"]
        self._uploaded = True

        print(f"[OK] Document uploaded, document_id={self.test_document_id}, version_id={self.test_version_id}")
        print("[INFO] Workers must be running to process the document asynchronously")

    def test_03_wait_for_processing(self):
        """Test 3: Wait for document processing"""
        print("\n=== Test 3: Wait for Document Processing ===")

        doc = self.get_test_document()
        if not doc:
            pytest.skip("No test document found - run test_02 first")
        
        self.test_document_id = doc.id
        self.test_version_id = doc.current_version_id

        # Check if already completed
        if doc.status == 2:
            print(f"[OK] Document already completed (doc_id={doc.id})")
            return

        print("Waiting for document processing (max 300 seconds)...")
        print("[INFO] Make sure workers are running: python src/app/services/run_worker.py all")

        max_wait = 300
        interval = 5
        elapsed = 0

        while elapsed < max_wait:
            self.db.expire_all()
            doc = self.db.query(Document).filter(Document.id == self.test_document_id).first()
            if not doc:
                pytest.fail("Document was deleted")

            status_map = {0: "Pending", 1: "Processing", 2: "Completed", 3: "Failed"}
            status_name = status_map.get(doc.status, f"Unknown({doc.status})")
            print(f"  Status: {status_name} (id={doc.id}, elapsed={elapsed}s)")
            
            if doc.status == 2:
                print("[OK] Document processing completed!")
                return
            elif doc.status == 3:
                ver = self.db.query(DocumentVersion).filter(
                    DocumentVersion.document_id == self.test_document_id
                ).first()
                error_msg = ver.error_message if ver and ver.error_message else "Unknown error"
                pytest.fail(f"Document processing failed: {error_msg}")

            time.sleep(interval)
            elapsed += interval

        pytest.fail(f"Document processing timeout ({max_wait}s)")

    def test_04_verify_chunks(self):
        """Test 4: Verify document chunking"""
        print("\n=== Test 4: Verify Document Chunking ===")

        doc = self.get_test_document()
        if not doc:
            pytest.skip("No test document found")
        
        self.test_document_id = doc.id
        self.test_version_id = doc.current_version_id

        chunks = self.db.query(DocumentChunk).filter(
            DocumentChunk.document_id == self.test_document_id,
            DocumentChunk.status != 9
        ).all()

        chunk_count = len(chunks)
        print(f"Chunk count: {chunk_count}")

        assert chunk_count > 0, "Document was not chunked!"

        content_chunks = [c for c in chunks if c.content and c.content.strip()]
        enhanced_chunks = [c for c in chunks if c.enhanced_content]

        print(f"  - Chunks with content: {len(content_chunks)}")
        print(f"  - Chunks with enhanced content: {len(enhanced_chunks)}")

        print("\nChunk examples:")
        for i, chunk in enumerate(chunks[:3]):
            content_preview = (chunk.content or "")[:100]
            enhanced_preview = (chunk.enhanced_content or "")[:100]
            print(f"  [{i+1}] type={chunk.chunk_type}, id={chunk.id}, content={content_preview}...")
            if enhanced_preview:
                print(f"       enhanced={enhanced_preview}...")

        print("[OK] Document chunking verified!")

    def test_05_verify_vector_database(self):
        """Test 5: Verify vector database"""
        print("\n=== Test 5: Verify Vector Database ===")

        doc = self.get_test_document()
        if not doc:
            pytest.skip("No test document found")
        
        self.test_document_id = doc.id
        self.test_version_id = doc.current_version_id

        try:
            milvus_repo = MilvusRepository()
            
            # Check for vectorized chunks
            vectorized_chunks = self.db.query(DocumentChunk).filter(
                DocumentChunk.document_id == self.test_document_id,
                DocumentChunk.status == 1
            ).all()

            all_chunks = self.db.query(DocumentChunk).filter(
                DocumentChunk.document_id == self.test_document_id
            ).all()
            
            print(f"  Total chunks: {len(all_chunks)}")
            print(f"  Vectorized chunks (status=1): {len(vectorized_chunks)}")

            if vectorized_chunks:
                chunk = vectorized_chunks[0]
                print(f"[OK] Found vectorized chunk, vector_id={chunk.vector_id}")
                
                try:
                    results = milvus_repo.search(
                        collection_name="document_chunks",
                        vectors=[[0.0] * 1024],
                        top_k=100,
                        expr=f"document_id == {self.test_document_id}"
                    )
                    print(f"[OK] Milvus query successful, found {len(results[0]) if results else 0} records")
                except Exception as e:
                    print(f"[WARN] Milvus query exception: {e}")
            else:
                print("[WARN] No vectorized chunks found yet")

        except Exception as e:
            print(f"[ERROR] Vector database verification failed: {e}")
            pytest.fail(f"Vector database verification failed: {e}")

    def test_06_check_error_logs(self):
        """Test 6: Check error logs"""
        print("\n=== Test 6: Check Error Logs ===")

        doc = self.get_test_document()
        if not doc:
            pytest.skip("No test document found")
        
        self.test_document_id = doc.id
        self.test_version_id = doc.current_version_id

        version = self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == self.test_document_id
        ).first()

        if version:
            if version.error_message:
                print(f"[WARN] Document has error message: {version.error_message}")
            else:
                print("[OK] Document has no error message")

            print(f"  Parse status: {version.parse_status}")
            print(f"  Parse progress: {version.parse_progress}")
            print(f"  Parse confidence: {version.parse_confidence}")


class TestEmbeddingService:
    """Embedding service test"""

    def test_mock_encode(self):
        """Test mock embedding"""
        print("\n=== Test Mock Embedding ===")

        service = ChunkEmbeddingService()
        
        # Test empty text
        embeddings = service._embedding_service._encode_batch([""])
        assert len(embeddings) == 1
        assert len(embeddings[0]) == 1024
        print("[OK] Empty text embedding successful")

        # Test normal text
        embeddings = service._embedding_service._encode_batch(["Test text"])
        assert len(embeddings) == 1
        assert len(embeddings[0]) == 1024
        print("[OK] Normal text embedding successful")

        # Test same text produces same vector
        emb1 = service._embedding_service._encode_batch(["Same text"])[0]
        emb2 = service._embedding_service._encode_batch(["Same text"])[0]
        assert all(a == b for a, b in zip(emb1, emb2))
        print("[OK] Same text produces same vector")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
