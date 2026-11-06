import json
from time import perf_counter

from httpx2 import Client

from src.application.models.article import Article
from src.application.models.article_assessment import ArticleAssessment

ARTICLE_ASSESSMENT_FORMAT = {
    "type": "object",
    "properties": {
        "rejected": {"type": "boolean"},
        "quality_comment": {"type": "string", "minLength": 1, "maxLength": 500},
        "summary": {
            "anyOf": [
                {"type": "string", "minLength": 1, "maxLength": 2000},
                {"type": "null"},
            ]
        },
    },
    "required": ["rejected", "quality_comment", "summary"],
    "additionalProperties": False,
}


class OllamaSummarizerClient:
    def __init__(self, http_client: Client, model: str, timeout_seconds: float):
        self.http_client = http_client
        self.model = model
        self.timeout_seconds = timeout_seconds

    def ai_summarize_article(self, article: Article) -> ArticleAssessment:
        parts: list[str] = []
        finished = False

        started_at = perf_counter()
        with self.http_client.stream(
            "POST",
            "/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Decide whether the Content is usable as a news article. "
                            "Reject it only when at least one of these conditions is "
                            "true: (1) Content is empty, a placeholder, or explicitly "
                            "says the article is unavailable or a draft; (2) Content "
                            "visibly ends in an unfinished sentence or clause, such "
                            "as 'announced a new' or 'voted on Tuesday, but'; "
                            "(3) Content has no complete factual claim about the "
                            "reported event beyond the Title. The Title alone cannot "
                            "make incomplete Content usable. Otherwise accept it. "
                            "Brief articles and articles covering several related "
                            "facts are usable. Do not reject for writing style, "
                            "organization, or lack of a formal conclusion. "
                            "If accepted, set rejected to false, summarize the "
                            "article's main facts in its original language in 1 to 4 "
                            "sentences and no more than 2000 characters, and use "
                            "quality_comment (1 to 500 characters) to state why it "
                            "is usable. An accepted article must have a non-null, "
                            "non-empty summary. Do not add facts. If rejected, set "
                            "rejected to true, name the failed condition in "
                            "quality_comment (1 to 500 characters), and set summary "
                            "to null. "
                            "Return only a JSON object with exactly these keys: "
                            "rejected, quality_comment, summary."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Title: {article.title}\n"
                            f"Content: {article.content}\n"
                            f"Language: {article.language}\n"
                        ),
                    },
                ],
                "stream": True,
                "format": ARTICLE_ASSESSMENT_FORMAT,
                "options": {"temperature": 0},
            },
            timeout=self.timeout_seconds,
        ) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue

                chunk = json.loads(line)
                if "error" in chunk:
                    raise RuntimeError("Ollama failed while generating a summary")

                parts.append(chunk.get("message", {}).get("content", ""))
                if chunk.get("done") is True:
                    finished = True
                    break

        content = "".join(parts).strip()
        if not finished or not content:
            raise ValueError("Ollama returned an incomplete or empty decision")

        try:
            decision = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError("Ollama returned invalid decision JSON") from exc

        if not isinstance(decision, dict) or set(decision) != {
            "rejected",
            "quality_comment",
            "summary",
        }:
            raise ValueError("Ollama returned an invalid decision")

        rejected = decision["rejected"]
        comment = decision["quality_comment"]
        summary = decision["summary"]
        if (
            not isinstance(rejected, bool)
            or not isinstance(comment, str)
            or not (isinstance(summary, str) or summary is None)
        ):
            raise ValueError("Ollama returned an invalid decision")

        return ArticleAssessment(
            rejected=rejected,
            quality_comment=comment.strip(),
            summary=summary.strip() if summary is not None else None,
            generation_duration_ms=max(0, round((perf_counter() - started_at) * 1000)),
        )

