from enum import Enum


class ReviewType(Enum):
    """The type of human review to perform."""

    APPROVE = "approve"
    FEEDBACK = "feedback"
    OVERWRITE = "overwrite"


class Status(Enum):
    """The status of the response."""

    APPROVED = "approved"
    IN_REVIEW = "in_review"
    REJECTED = "rejected"
