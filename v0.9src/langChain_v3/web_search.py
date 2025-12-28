from typing import Dict, List


def search_web(query: str, k: int = 10) -> List[Dict[str, str]]:
    """
    Web search hook used by hybrid_search_rerank.

    Expected fields per result (best effort):
    - title
    - url
    - snippet (short summary or content)
    """
    raise NotImplementedError(
        "Wire this to your web search provider (SerpAPI, Tavily, Bing, etc.)."
    )
