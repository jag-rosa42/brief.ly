from src.application.models.article import Article
from src.application.ports.ai_summarizer import ArticleSummarizerPort
from src.application.ports.content_management import ArticleContentManagementPort

# The command entry point creates the HTTP clients and passes them to this use case.


class SummarizeArticles:
    def __init__(
        self,
        content_management: ArticleContentManagementPort,
        ai_summarizer: ArticleSummarizerPort,
        llm_model: str,
        batch_size: int,
    ) -> None:
        if batch_size < 1:
            raise ValueError("Article batch size must be positive")
        self.content_management = content_management
        self.ai_summarizer = ai_summarizer
        self.llm_model = llm_model
        self.batch_size = batch_size

    def execute(self) -> None:
        while True:
            articles: list[Article] = self.content_management.list_missing_articles(
                self.batch_size
            )
            if not articles:
                return

            for article in articles:
                assessment = self.ai_summarizer.ai_summarize_article(article)
                self.content_management.save_article_assessment(
                    article.id, assessment, self.llm_model
                )
