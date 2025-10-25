from enum import Enum


class CreateStocktakeRequestStatus(str, Enum):
    COMPLETED = "COMPLETED"
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"

    def __str__(self) -> str:
        return str(self.value)
