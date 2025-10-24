from chromadb import Documents, EmbeddingFunction, Embeddings
from chromadb.api.types import Space
from typing import Optional, List, cast, Dict, Any
from google.genai import types
from chromadb.utils.embedding_functions.schemas import validate_config_schema
import numpy as np
import numpy.typing as npt
import os


class GoogleGenAiEmbeddingFunction(EmbeddingFunction[Documents]):
    """To use this EmbeddingFunction, you must have the google.generativeai Python package installed and have a Google API key."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "models/embedding-001",
        task_type: str = "RETRIEVAL_DOCUMENT",
        api_key_env_var: str = "CHROMA_GOOGLE_GENAI_API_KEY",
    ):
        """
        Initialize the GoogleGenerativeAiEmbeddingFunction.

        Args:
            api_key_env_var (str, optional): Environment variable name that contains your API key for the Google Generative AI API.
                Defaults to "CHROMA_GOOGLE_GENAI_API_KEY".
            model_name (str, optional): The name of the model to use for text embeddings.
                Defaults to "models/embedding-001".
            task_type (str, optional): The task type for the embeddings.
                Use "RETRIEVAL_DOCUMENT" for embedding documents and "RETRIEVAL_QUERY" for embedding queries.
                Defaults to "RETRIEVAL_DOCUMENT".
        """
        try:
            from google import genai
        except ImportError:
            raise ValueError(
                "The Google Generative AI python package is not installed. Please install it with `pip install google-generativeai`"
            )

        self.api_key_env_var = api_key_env_var
        self.api_key = api_key or os.getenv(api_key_env_var)
        if not self.api_key:
            raise ValueError(f"The {api_key_env_var} environment variable is not set.")

        self.model_name = model_name
        self.task_type = task_type

        self._genai = genai.Client(api_key=self.api_key)

    def __call__(self, input: Documents) -> Embeddings:
        """
        Generate embeddings for the given documents.

        Args:
            input: Documents or images to generate embeddings for.

        Returns:
            Embeddings for the documents.
        """
        # Google Generative AI only works with text documents
        if not all(isinstance(item, str) for item in input):
            raise ValueError(
                "Google Generative AI only supports text documents, not images"
            )

        embeddings_list: List[npt.NDArray[np.float32]] = []
        for text in input:
            embedding_result = self._genai.models.embed_content(
                model=self.model_name,
                contents=text,
                config=types.EmbedContentConfig(task_type=self.task_type),
            )
            if embedding_result.embeddings and len(embedding_result.embeddings) > 0:
                embeddings_list.append(
                    np.array(embedding_result.embeddings[0].values, dtype=np.float32)
                )

        # Convert to the expected Embeddings type (List[Vector])
        return cast(Embeddings, embeddings_list)

    @staticmethod
    def name() -> str:
        return "google_genai"

    def default_space(self) -> Space:
        return "cosine"

    def supported_spaces(self) -> List[Space]:
        return ["cosine", "l2", "ip"]

    @staticmethod
    def build_from_config(config: Dict[str, Any]) -> "EmbeddingFunction[Documents]":
        api_key_env_var = config.get("api_key_env_var")
        model_name = config.get("model_name")
        task_type = config.get("task_type")

        if api_key_env_var is None or model_name is None or task_type is None:
            assert False, "This code should not be reached"

        return GoogleGenAiEmbeddingFunction(
            api_key_env_var=api_key_env_var, model_name=model_name, task_type=task_type
        )

    def get_config(self) -> Dict[str, Any]:
        return {
            "api_key_env_var": self.api_key_env_var,
            "model_name": self.model_name,
            "task_type": self.task_type,
        }

    def validate_config_update(
        self, old_config: Dict[str, Any], new_config: Dict[str, Any]
    ) -> None:
        if "model_name" in new_config:
            raise ValueError(
                "The model name cannot be changed after the embedding function has been initialized."
            )
        if "task_type" in new_config:
            raise ValueError(
                "The task type cannot be changed after the embedding function has been initialized."
            )

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> None:
        """
        Validate the configuration using the JSON schema.

        Args:
            config: Configuration to validate

        Raises:
            ValidationError: If the configuration does not match the schema
        """
        validate_config_schema(config, "google_generative_ai")
