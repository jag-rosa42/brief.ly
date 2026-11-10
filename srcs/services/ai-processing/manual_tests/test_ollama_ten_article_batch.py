"""Explicit ten-article worker test with real Ollama and fake Content Management."""

import json
from contextlib import closing
from dataclasses import dataclass, field
from time import perf_counter

import httpx2 as httpx
from shared_auth import DownstreamClient

from scripts.try_ollama_workflow import (
    DEFAULT_MODEL,
    DEFAULT_OLLAMA_URL,
    StaticTokenProvider,
)
from src.infrastructure.config.worker import WorkerSettings
from src.worker import run_worker

TOPIC_ID = "local-news"

COMPLETE_ARTICLES = [
    (
        "City library opens a second reading room",
        "The city library opened a second reading room on Monday after a three-month "
        "renovation. The new room has forty seats, improved lighting, and a quiet "
        "study area. Library staff said the renovation was funded by the city council "
        "and completed on schedule. The room is open during the library's usual hours. "
        "On opening day, staff showed visitors the new desks and explained how to "
        "reserve a seat. The library will review usage after the first month before "
        "deciding whether to extend evening access.",
    ),
    (
        "Riverside park reopens after path repairs",
        "Riverside park reopened on Tuesday after workers repaired a damaged walking "
        "path. The city closed the path for two weeks while crews replaced broken "
        "paving and improved drainage near the river. The playground and sports field "
        "remained open during the work. City officials said the repaired route is now "
        "accessible from both main entrances. They asked visitors to stay on the "
        "marked path while new grass grows beside it. A final inspection was completed "
        "on Monday, and no further closures are planned.",
    ),
    (
        "Museum adds weekend hours for spring exhibition",
        "The town museum will open an extra two hours on Saturdays during its spring "
        "exhibition, starting this weekend. The exhibition brings together photographs "
        "and maps showing how the town centre changed over the past century. Museum "
        "staff said the extra hours respond to visitors who cannot attend on weekdays. "
        "Admission prices will stay the same, and tickets can be bought at the door. "
        "The longer Saturday schedule will run through the exhibition's final day in "
        "June. Regular weekday opening hours are unchanged.",
    ),
    (
        "Bus operator adds morning service to station",
        "The local bus operator added a morning trip between the eastern district "
        "and the railway station on Wednesday. The new departure leaves the district "
        "at 7:15 and reaches the station before the first express train. The operator "
        "said the timetable change followed a survey of commuters earlier this year. "
        "Existing afternoon trips are unaffected. Printed schedules are available "
        "on buses, and the updated timetable is posted at each stop. The operator "
        "will review passenger numbers after eight weeks.",
    ),
    (
        "Water utility finishes pipe replacement",
        "The municipal water utility finished replacing an ageing pipe under Market "
        "Street on Thursday. Crews installed a new section over four nights to limit "
        "traffic disruption. The utility said households had been warned before two "
        "short water interruptions, and service was restored after each overnight "
        "shift. Workers tested the new pipe before reopening the road. The project "
        "was part of a planned maintenance programme for the town centre. The utility "
        "said no further work is expected on Market Street this month.",
    ),
    (
        "Community festival announces summer programme",
        "Organisers of the community festival announced a summer programme on Friday. "
        "The three-day event will include local music, food stalls, and workshops in "
        "the central square. The organisers said entry to daytime events will be free, "
        "while evening concerts will require tickets. Volunteers will help visitors "
        "find accessible routes between venues. A full schedule is available at the "
        "community centre. The festival is supported by local businesses and will "
        "finish with a public concert on Sunday evening.",
    ),
    (
        "Farmers market moves to larger site",
        "The weekly farmers market moved to the old depot site on Saturday to make "
        "room for more stalls. Market organisers said twenty growers and food makers "
        "attended the first session at the new location, compared with fourteen at "
        "the previous site. The market will continue to open every Saturday morning. "
        "Signs direct visitors from the town centre, and a temporary bicycle parking "
        "area has been added beside the entrance. Organisers said they will gather "
        "feedback from traders and shoppers before finalising the site layout.",
    ),
]

REJECTED_ARTICLES = [
    ("Council meeting report unavailable", "Article unavailable. Please try again."),
    ("School renovation update", "The school renovation began on Monday, but"),
    ("Hospital announcement", "Home | News | Sign in | Subscribe | Cookie settings"),
]

ARTICLE_CONTENTS = [
    COMPLETE_ARTICLES[0],
    REJECTED_ARTICLES[0],
    COMPLETE_ARTICLES[1],
    COMPLETE_ARTICLES[2],
    REJECTED_ARTICLES[1],
    COMPLETE_ARTICLES[3],
    COMPLETE_ARTICLES[4],
    COMPLETE_ARTICLES[5],
    REJECTED_ARTICLES[2],
    COMPLETE_ARTICLES[6],
]
ARTICLES = [
    {
        "article_id": f"123e4567-e89b-12d3-a456-426614174{index:03d}",
        "title": title,
        "content": content,
        "language": "en",
        "topic_id": TOPIC_ID,
    }
    for index, (title, content) in enumerate(ARTICLE_CONTENTS)
]
ARTICLE_IDS = {article["article_id"] for article in ARTICLES}
ARTICLES_BY_ID = {article["article_id"]: article for article in ARTICLES}
REJECTED_IDS = {ARTICLES[index]["article_id"] for index in (1, 4, 8)}
ACCEPTED_IDS = ARTICLE_IDS - REJECTED_IDS


@dataclass
class FakeContentManagement:
    assessments: dict[str, dict[str, object]] = field(default_factory=dict)
    missing_pages: list[list[str]] = field(default_factory=list)
    topic_article_ids: list[str] = field(default_factory=list)
    topic_summary: dict[str, object] | None = None

    def respond(self, request: httpx.Request) -> httpx.Response:
        assert "Authorization" not in request.headers
        path = request.url.path

        if request.method == "GET" and path == "/internal/v1/articles":
            assert request.url.params.get("limit") == "5" or (
                request.url.params.get("topic_id") == TOPIC_ID
                and request.url.params.get("limit") == "25"
            )
            if request.url.params.get("summary") == "missing":
                pending = [
                    article
                    for article in ARTICLES
                    if article["article_id"] not in self.assessments
                ]
                page = pending[:5]
                self.missing_pages.append([article["article_id"] for article in page])
                return httpx.Response(200, json={"items": page})

            assert request.url.params.get("topic_id") == TOPIC_ID
            assert request.url.params.get("cursor") is None
            items = [
                {"article_id": article_id, "summary": assessment["text"]}
                for article_id, assessment in self.assessments.items()
                if assessment["text"] is not None
            ]
            self.topic_article_ids = [
                article_id
                for article_id, assessment in self.assessments.items()
                if assessment["text"] is not None
            ]
            return httpx.Response(200, json={"items": items})

        if request.method == "PUT" and path.startswith("/internal/v1/articles/"):
            assert path.endswith("/summary")
            article_id = path.split("/")[4]
            assert article_id in ARTICLE_IDS
            assert article_id not in self.assessments
            assessment = json.loads(request.content)
            assert set(assessment) == {
                "text",
                "rejected",
                "quality_comment",
                "llm_model",
                "generation_duration_ms",
            }
            assert assessment["llm_model"] == DEFAULT_MODEL
            assert isinstance(assessment["generation_duration_ms"], int)
            assert assessment["generation_duration_ms"] >= 0
            self.assessments[article_id] = assessment
            article = ARTICLES_BY_ID[article_id]
            print(f"\nArticle: {article['title']}")
            print(f"Content: {article['content']}")
            print(f"Rejected: {assessment['rejected']}")
            print(f"Quality comment: {assessment['quality_comment']}")
            print(f"Summary: {assessment['text']}")
            return httpx.Response(200)

        if request.method == "GET" and path == "/internal/v1/topics":
            assert len(self.assessments) == len(ARTICLES)
            return httpx.Response(200, json=[{"id": TOPIC_ID}])

        if request.method == "PUT" and path == (
            f"/internal/v1/topics/{TOPIC_ID}/summary"
        ):
            assert self.topic_summary is None
            self.topic_summary = json.loads(request.content)
            return httpx.Response(200)

        raise AssertionError(
            f"Unexpected Content Management request: {request.method} {path}"
        )


def test_ten_articles_with_three_rejections() -> None:
    settings = WorkerSettings(
        _env_file=None,
        CONTENT_MANAGEMENT_BASE_URL="http://content-management",
        OLLAMA_BASE_URL=DEFAULT_OLLAMA_URL,
        OLLAMA_MODEL=DEFAULT_MODEL,
        ARTICLE_BATCH_SIZE=5,
    )
    fake = FakeContentManagement()
    started = perf_counter()
    with (
        closing(
            DownstreamClient(
                "content-management",
                settings.CONTENT_MANAGEMENT_BASE_URL,
                transport=httpx.MockTransport(fake.respond),
            )
        ) as content_client,
        httpx.Client(base_url=settings.OLLAMA_BASE_URL) as ollama_client,
    ):
        run_worker(settings, content_client, ollama_client, StaticTokenProvider())
    elapsed_seconds = perf_counter() - started

    assert fake.missing_pages == [
        [article["article_id"] for article in ARTICLES[:5]],
        [article["article_id"] for article in ARTICLES[5:]],
        [],
    ]
    assert set(fake.assessments) == ARTICLE_IDS
    for article_id in REJECTED_IDS:
        assessment = fake.assessments[article_id]
        assert assessment["rejected"] is True, assessment["quality_comment"]
        assert assessment["text"] is None
    for article_id in ACCEPTED_IDS:
        assessment = fake.assessments[article_id]
        assert assessment["rejected"] is False, assessment["quality_comment"]
        assert isinstance(assessment["text"], str) and assessment["text"].strip()

    assert set(fake.topic_article_ids) == ACCEPTED_IDS
    assert fake.topic_summary is not None
    assert fake.topic_summary["llm_model"] == DEFAULT_MODEL
    assert isinstance(fake.topic_summary["text"], str)
    assert fake.topic_summary["text"].strip()
    print(f"Processed 10 articles: 7 accepted, 3 rejected in {elapsed_seconds:.2f}s")
