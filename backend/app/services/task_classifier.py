TASK_TYPE_RESEARCH = "research"
TASK_TYPE_SUMMARY = "summary"
TASK_TYPE_COMPARISON = "comparison"
TASK_TYPE_GENERAL = "general"


def classify_task(title: str, description: str | None = None) -> str:
    content = f"{title} {description or ''}".lower()

    comparison_keywords = (
        "compare",
        "comparison",
        "vs",
        "versus",
        "difference",
        "differences",
        "pros and cons",
        "better than",
    )
    summary_keywords = (
        "summarize",
        "summary",
        "summarise",
        "brief",
        "recap",
        "tldr",
        "tl;dr",
    )
    research_keywords = (
        "research",
        "investigate",
        "analysis",
        "analyze",
        "analyse",
        "study",
        "explore",
        "find information",
        "look into",
    )

    if any(keyword in content for keyword in comparison_keywords):
        return TASK_TYPE_COMPARISON

    if any(keyword in content for keyword in summary_keywords):
        return TASK_TYPE_SUMMARY

    if any(keyword in content for keyword in research_keywords):
        return TASK_TYPE_RESEARCH

    return TASK_TYPE_GENERAL
