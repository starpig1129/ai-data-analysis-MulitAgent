from langchain_groq import ChatGroq

from .base import BaseProvider


class ChatGroqProvider(BaseProvider):
    """Provider for ChatGroq models."""

    def get_model_class(self) -> type:
        """Returns the ChatGroq class."""
        return ChatGroq
