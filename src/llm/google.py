from langchain_google_genai import ChatGoogleGenerativeAI

from .base import BaseProvider


class GoogleProvider(BaseProvider):
    """Provider for Google models."""

    def get_model_class(self) -> type:
        """Returns the ChatGoogleGenerativeAI class."""
        return ChatGoogleGenerativeAI
