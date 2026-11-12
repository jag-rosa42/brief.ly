class AnswerValidationError(ValueError):
    """An invalid generated answer that can be supplied to a corrective retry.

    Keep the answer out of the exception message so worker logs contain only
    the validation reason. The use case retains it only for the current batch.
    """

    def __init__(self, reason: str, previous_answer: str) -> None:
        super().__init__(reason)
        self.previous_answer = previous_answer
