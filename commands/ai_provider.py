import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("EVA")


class AIProvider(ABC):
    @abstractmethod
    def generate_response(self, messages: list) -> str:
        pass

    @abstractmethod
    def get_available_models(self) -> list:
        pass

    @abstractmethod
    def change_model(self, model_name: str) -> str:
        pass

    @property
    @abstractmethod
    def current_model(self) -> str:
        pass


class OllamaProvider(AIProvider):
    def __init__(self, ollama_integration):
        self._ollama = ollama_integration

    def generate_response(self, messages: list) -> str:
        last_user_msg = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )
        return self._ollama.process_conversation(last_user_msg)

    def get_available_models(self) -> list:
        return self._ollama.get_installed_models(force_refresh=True)

    def change_model(self, model_name: str) -> str:
        return self._ollama.change_model(model_name)

    @property
    def current_model(self) -> str:
        return self._ollama.current_model

    @property
    def provider_name(self) -> str:
        return "Ollama"

    def list_models_formatted(self) -> str:
        models = self.get_available_models()
        if not models:
            return "No se encontraron modelos Ollama instalados."
        lines = [f"Modelos {self.provider_name} disponibles:\n"]
        for i, name in enumerate(models, start=1):
            marker = " (activo)" if name == self.current_model else ""
            lines.append(f"  {i}. {name}{marker}")
        return "\n".join(lines)


class OpenRouterProvider(AIProvider):
    OPENROUTER_MODELS = [
        "openrouter/free",
        "deepseek/deepseek-r1:free",
        "qwen/qwen3.6-plus-preview:free",
        "meta-llama/llama-3.3-70b-instruct:free",
    ]

    def __init__(self, api_key: str, model_name: str = "openrouter/free"):
        from openai import OpenAI

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "EVA Asistente",
            },
        )
        self._current_model = model_name
        self._api_key = api_key

    def generate_response(self, messages: list) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self._current_model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error con OpenRouter: {e}")
            return (
                f"Error con OpenRouter: {str(e)}. "
                "Verifica tu API key o tu conexion a internet. "
                "Usa el comando 'modelo' para cambiar a Ollama."
            )

    def get_available_models(self) -> list:
        return list(self.OPENROUTER_MODELS)

    def change_model(self, model_name: str) -> str:
        if model_name not in self.OPENROUTER_MODELS:
            return (
                f"Modelo '{model_name}' no disponible. "
                f"Opciones: {', '.join(self.OPENROUTER_MODELS)}"
            )
        self._current_model = model_name
        logger.info(f"Modelo de OpenRouter cambiado a: {model_name}")
        return f"Modelo de OpenRouter cambiado a {model_name}"

    @property
    def current_model(self) -> str:
        return self._current_model

    @property
    def provider_name(self) -> str:
        return "OpenRouter"

    def list_models_formatted(self) -> str:
        models = self.OPENROUTER_MODELS
        lines = [f"Modelos {self.provider_name} disponibles:\n"]
        for i, name in enumerate(models, start=1):
            marker = " (activo)" if name == self.current_model else ""
            lines.append(f"  {i}. {name}{marker}")
        return "\n".join(lines)
