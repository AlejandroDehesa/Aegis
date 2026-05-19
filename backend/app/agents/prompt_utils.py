def build_retrieved_context_block(retrieved_context: str | None) -> str:
    if not retrieved_context:
        return ""

    return (
        "Available document context:\n"
        f"{retrieved_context}\n\n"
        "Use this document context when it is relevant. If context is insufficient, state assumptions.\n\n"
    )
