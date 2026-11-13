from src.application.models.answer_validation_error import AnswerValidationError


class GenerationLimitError(AnswerValidationError):
    """A truncated answer requiring a shorter corrective generation."""
