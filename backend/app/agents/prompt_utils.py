def build_retrieved_context_block(retrieved_context: str | None) -> str:
    if not retrieved_context:
        return ""

    return f"Relevant retrieved context:\n{retrieved_context}\n\n"
