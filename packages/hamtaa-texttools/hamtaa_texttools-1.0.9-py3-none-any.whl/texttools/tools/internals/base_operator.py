from typing import TypeVar, Type, Any
import json
import re
import math
import logging

from pydantic import BaseModel
from openai import OpenAI, AsyncOpenAI

# Base Model type for output models
T = TypeVar("T", bound=BaseModel)

# Configure logger
logger = logging.getLogger("base_operator")
logger.setLevel(logging.INFO)


class BaseOperator:
    def __init__(self, client: OpenAI | AsyncOpenAI, model: str):
        self.client = client
        self.model = model

    def _build_user_message(self, prompt: str) -> dict[str, str]:
        return {"role": "user", "content": prompt}

    def _clean_json_response(self, response: str) -> str:
        """
        Clean JSON response by removing code block markers and whitespace.
        Handles cases like:
        - ```json{"result": "value"}```
        """
        stripped = response.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", stripped)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        return cleaned.strip()

    def _convert_to_output_model(
        self, response_string: str, output_model: Type[T]
    ) -> Type[T]:
        """
        Convert a JSON response string to output model.

        Args:
            response_string: The JSON string (may contain code block markers)
            output_model: Your Pydantic output model class (e.g., StrOutput, ListStrOutput)

        Returns:
            Instance of your output model
        """
        # Clean the response string
        cleaned_json = self._clean_json_response(response_string)

        # Fix Python-style booleans
        cleaned_json = cleaned_json.replace("False", "false").replace("True", "true")

        # Convert string to Python dictionary
        response_dict = json.loads(cleaned_json)

        # Convert dictionary to output model
        return output_model(**response_dict)

    def _extract_logprobs(self, completion: dict) -> list[dict[str, Any]]:
        logprobs_data = []
        ignore_pattern = re.compile(r'^(result|[\s\[\]\{\}",:]+)$')

        for choice in completion.choices:
            if not getattr(choice, "logprobs", None):
                logger.error("logprobs is not avalible in the chosen model.")
                return []

            for logprob_item in choice.logprobs.content:
                if ignore_pattern.match(logprob_item.token):
                    continue
                token_entry = {
                    "token": logprob_item.token,
                    "prob": round(math.exp(logprob_item.logprob), 8),
                    "top_alternatives": [],
                }
                for alt in logprob_item.top_logprobs:
                    if ignore_pattern.match(alt.token):
                        continue
                    token_entry["top_alternatives"].append(
                        {
                            "token": alt.token,
                            "prob": round(math.exp(alt.logprob), 8),
                        }
                    )
                logprobs_data.append(token_entry)

        return logprobs_data
