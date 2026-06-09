from __future__ import annotations

import re


def build_retrieved_context_block(retrieved_context: str | None) -> str:
    if not retrieved_context:
        return ""

    return (
        "Available document context:\n"
        f"{retrieved_context}\n\n"
        "Use this document context when it is relevant. If context is insufficient, state assumptions.\n\n"
    )


def build_evidence_section_from_context(retrieved_context: str | None, max_items: int = 3) -> str:
    if not retrieved_context or not retrieved_context.strip():
        return ""

    sections = [section.strip() for section in retrieved_context.split("\n\n---\n\n") if section.strip()]
    evidence_items: list[str] = []

    for section in sections:
        if len(evidence_items) >= max_items:
            break

        document_match = re.search(r"Document:\s*(.+)", section, flags=re.IGNORECASE)
        chunk_match = re.search(r"Chunk(?: Index)?:\s*(.+)", section, flags=re.IGNORECASE)
        score_match = re.search(r"(?:Relevance score|Score):\s*([0-9.]+)", section, flags=re.IGNORECASE)
        content_match = re.search(r"Content:\s*(.+)", section, flags=re.IGNORECASE | re.DOTALL)

        document_name = document_match.group(1).strip() if document_match else "Unknown document"
        chunk_label = chunk_match.group(1).strip() if chunk_match else "N/A"
        score_label = score_match.group(1).strip() if score_match else "N/A"
        snippet = ""
        if content_match:
            snippet = " ".join(content_match.group(1).split())
        if len(snippet) > 220:
            snippet = f"{snippet[:220].rstrip()}..."
        if not snippet:
            snippet = "No snippet available."

        evidence_items.append(
            "\n".join(
                [
                    f"{len(evidence_items) + 1}. Documento / Document: {document_name}",
                    f"   Fragmento / Snippet (chunk {chunk_label}, score {score_label}): {snippet}",
                    "   Uso en el analisis / Use in analysis: This evidence informs the recommendation and risk statements.",
                ]
            )
        )

    if not evidence_items:
        return ""

    return (
        "\n\n## Evidencias usadas / Evidence used\n"
        + "\n".join(evidence_items)
    )
