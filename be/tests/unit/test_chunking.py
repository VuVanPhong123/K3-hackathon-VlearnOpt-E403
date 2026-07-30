from app.services.chunking_service import ChunkingService


def test_chunk_ids_are_deterministic() -> None:
    pages = [
        {
            "page_number": 1,
            "blocks": [{"index": 0, "text": "RAG citation evidence", "bbox": [0, 0, 10, 10]}],
        }
    ]
    sections = [{"section_id": "doc-v1-p0001", "title": "Page 1", "start_page": 1, "end_page": 1}]
    chunks = ChunkingService().create_chunks("doc", 1, pages, sections)
    assert chunks[0]["chunk_id"] == "doc-v1-p0001-c0001"
    assert chunks[0]["page_number"] == 1
