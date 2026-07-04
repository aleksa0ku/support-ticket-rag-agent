from app.ingest import load_doc_chunks, load_ticket_chunks


def test_doc_chunks_have_expected_shape():
    chunks = load_doc_chunks()
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk["metadata"]["doc_id"]
        assert chunk["metadata"]["source_type"] == "doc"
        assert chunk["text"].strip()


def test_doc_chunks_cover_all_docs():
    chunks = load_doc_chunks()
    doc_ids = {c["metadata"]["doc_id"] for c in chunks}
    assert "billing-plans" in doc_ids
    assert "security-2fa" in doc_ids
    assert len(doc_ids) == 15


def test_ticket_chunks_reference_doc_ids():
    doc_chunks = load_doc_chunks()
    known_doc_ids = {c["metadata"]["doc_id"] for c in doc_chunks}

    ticket_chunks = load_ticket_chunks()
    assert len(ticket_chunks) == 60
    for chunk in ticket_chunks:
        assert chunk["metadata"]["source_type"] == "ticket"
        doc_id = chunk["metadata"]["doc_id"]
        assert doc_id in known_doc_ids
