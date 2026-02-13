"""
GRS AI API Client - универсальный клиент для работы с GRS AI API

Использование:
    from Блоки.интеграции_ии import GRSAIClient
    
    client = GRSAIClient(api_key="your_key")
    response = client.chat(
        messages=[{"role": "user", "content": "Привет!"}],
        model="gpt-4o-mini"
    )
    print(response)

Документация: https://grsai.com/dashboard/documents/chat
"""

import os
import json
import logging
from typing import List, Dict, Optional, Generator, Any
import requests
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class GRSAIConfig:
    """Конфигурация для GRS AI API"""
    api_key: str
    base_url: str = "https://grsaiapi.com"
    default_model: str = "gpt-4o-mini"
    timeout: int = 60
    fallback_models: List[str] = None
    
    def __post_init__(self):
        if self.fallback_models is None:
            self.fallback_models = ["gpt-4o-mini", "gemini-2.5-flash", "gemini-2.5-flash-lite"]


class GRSAIClient:
    """
    Универсальный клиент для работы с GRS AI API
    
    Основные возможности:
    - Обычный и потоковый режим
    - Автоматическая обработка кодировки (UTF-8)
    - Парсинг различных форматов ответов
    - Fallback на другие модели при ошибках
    - Обработка ошибок API
    """
    
    # Доступные модели
    FAST_MODELS = ["gpt-4o-mini", "gemini-2.5-flash", "gemini-2.5-flash-lite"]
    POWERFUL_MODELS = ["gemini-2.5-pro", "gemini-3-pro", "gpt-4o-all"]
    SIMPLE_MODELS = ["nano-banana-fast", "nano-banana"]
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[GRSAIConfig] = None):
        """
        Инициализация клиента
        
        Args:
            api_key: API ключ (если не указан, берется из переменной окружения GRS_AI_API_KEY)
            config: Объект конфигурации (опционально)
        """
        if config:
            self.config = config
        else:
            api_key = api_key or os.getenv("GRS_AI_API_KEY")
            if not api_key:
                raise ValueError("API key must be provided or set in GRS_AI_API_KEY environment variable")
            
            base_url = os.getenv("GRS_AI_API_URL", "https://grsaiapi.com")
            self.config = GRSAIConfig(api_key=api_key, base_url=base_url)
        
        self.endpoint = f"{self.config.base_url}/v1/chat/completions"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        })
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_fallback: bool = True
    ) -> str:
        """
        Отправка запроса к GRS AI API (обычный режим)
        
        Args:
            messages: Список сообщений в формате [{"role": "user", "content": "текст"}]
            model: Название модели (если не указано, используется default_model)
            stream: Потоковый режим (по умолчанию False)
            temperature: Температура генерации (опционально)
            max_tokens: Максимальное количество токенов (опционально)
            use_fallback: Использовать fallback модели при ошибке
        
        Returns:
            Текст ответа от AI
        
        Raises:
            Exception: При ошибке API или пустом ответе
        """
        if stream:
            raise ValueError("For streaming use chat_stream() method")
        
        model = model or self.config.default_model
        
        try:
            response_text = self._make_request(messages, model, stream=False, temperature=temperature, max_tokens=max_tokens)
            return response_text
        
        except Exception as e:
            logger.error(f"Error with model {model}: {e}")
            
            if use_fallback and self.config.fallback_models:
                # Пробуем остальные модели (включая из fallback_models, кроме той что уже упала)
                to_try = [m for m in self.config.fallback_models if m != model]
                if not to_try:
                    to_try = [m for m in ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gpt-4o-mini"] if m != model]
                logger.info("Trying fallback models: %s", to_try)
                for fallback_model in to_try:
                    try:
                        response_text = self._make_request(messages, fallback_model, stream=False, temperature=temperature, max_tokens=max_tokens)
                        logger.info("Success with fallback model: %s", fallback_model)
                        return response_text
                    except Exception as fallback_error:
                        logger.error("Fallback model %s failed: %s", fallback_model, fallback_error)
                        continue
            
            raise Exception(f"All models failed. Last error: {e}")
    
    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Generator[str, None, None]:
        """
        Отправка запроса к GRS AI API (потоковый режим)
        
        Args:
            messages: Список сообщений
            model: Название модели
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов
        
        Yields:
            Части текста по мере генерации
        """
        model = model or self.config.default_model
        
        data = {
            "model": model,
            "messages": messages,
            "stream": True
        }
        
        if temperature is not None:
            data["temperature"] = temperature
        if max_tokens is not None:
            data["max_tokens"] = max_tokens
        
        try:
            response = self.session.post(
                self.endpoint,
                json=data,
                stream=True,
                timeout=self.config.timeout
            )
            response.encoding = "utf-8"  # КРИТИЧНО для кириллицы
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    if line.startswith(b"data: "):
                        chunk = line[6:].decode("utf-8")
                        if chunk == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(chunk)
                            delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if delta:
                                yield delta
                        except json.JSONDecodeError:
                            continue
        
        except requests.exceptions.Timeout:
            raise Exception(f"Request timeout after {self.config.timeout} seconds")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
    
    def _make_request(
        self,
        messages: List[Dict[str, str]],
        model: str,
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Внутренний метод для выполнения запроса
        
        Args:
            messages: Список сообщений
            model: Название модели
            stream: Потоковый режим
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов
        
        Returns:
            Текст ответа
        """
        # Формируем тело запроса - ТОЛЬКО поддерживаемые поля
        data = {
            "model": model,
            "messages": messages,
            "stream": stream
        }
        
        # Добавляем опциональные параметры только если они указаны
        if temperature is not None:
            data["temperature"] = temperature
        if max_tokens is not None:
            data["max_tokens"] = max_tokens
        
        try:
            response = self.session.post(
                self.endpoint,
                json=data,
                timeout=self.config.timeout
            )
            response.encoding = "utf-8"  # КРИТИЧНО для кириллицы
            response.raise_for_status()
            
            result = response.json()
            
            # Проверка на ошибку API
            if result.get("code") != 0 and "code" in result:
                error_msg = result.get("msg", "Unknown error")
                raise Exception(f"GRS AI API Error: {error_msg}")
            
            # Парсинг ответа - проверяем все возможные форматы
            response_text = self._parse_response(result)
            
            if not response_text:
                raise Exception("Empty response from API")
            
            return response_text
        
        except requests.exceptions.Timeout:
            raise Exception(f"Request timeout after {self.config.timeout} seconds")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
    
    def _parse_response(self, result: Dict[str, Any]) -> str:
        """
        Парсинг ответа от GRS AI API
        
        GRS AI может возвращать ответ в разных форматах.
        Проверяем все возможные варианты.
        
        Args:
            result: JSON ответ от API
        
        Returns:
            Извлеченный текст ответа
        """
        # Порядок проверки важен - от наиболее вероятного к редким
        text = (
            result.get("choices", [{}])[0].get("message", {}).get("content") or
            result.get("data", {}).get("output", {}).get("text") or
            result.get("output", {}).get("text") or
            result.get("response") or
            result.get("content") or
            result.get("text") or
            ""
        )
        
        # Если текст пришел в искаженной кодировке (Latin-1 вместо UTF-8)
        if text and self._is_encoding_broken(text):
            try:
                text = text.encode("latin-1").decode("utf-8")
                logger.warning("Fixed encoding issue in response")
            except (UnicodeDecodeError, UnicodeEncodeError):
                logger.warning("Could not fix encoding issue")
        
        return text
    
    @staticmethod
    def _is_encoding_broken(text: str) -> bool:
        """
        Проверка, искажена ли кодировка текста
        
        Args:
            text: Текст для проверки
        
        Returns:
            True если кодировка искажена
        """
        # Характерные символы искаженной кириллицы
        broken_chars = ["Ð", "Ñ", "Â", "Ã", "Ð¸", "Ð°"]
        return any(char in text for char in broken_chars)
    
    def simple_ask(self, question: str, system_prompt: Optional[str] = None, model: Optional[str] = None) -> str:
        """
        Упрощенный метод для быстрых запросов
        
        Args:
            question: Вопрос пользователя
            system_prompt: Системный промпт (опционально)
            model: Модель для использования
        
        Returns:
            Ответ от AI
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": question})
        
        return self.chat(messages=messages, model=model)
    
    @classmethod
    def get_available_models(cls) -> Dict[str, List[str]]:
        """
        Получить список доступных моделей
        
        Returns:
            Словарь с категориями моделей
        """
        return {
            "fast": cls.FAST_MODELS,
            "powerful": cls.POWERFUL_MODELS,
            "simple": cls.SIMPLE_MODELS
        }

    IMAGE_MODELS = ["gpt-image-1", "gpt-image-1.5", "nano-banana-pro", "flux"]

    def generate_image(
        self,
        prompt: str,
        model: str = "gpt-image-1",
        size: str = "1024x1024",
        image_urls: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Генерация изображения через GRS AI Draw API.
        Endpoint: /v1/draw/completions

        image_urls: список URL референсных изображений (или data URL с base64).
                    Первое изображение можно использовать как лицо/персонажа для переноса в сцену.
        """
        base = self.config.base_url.rstrip("/")
        urls = image_urls if image_urls else []
        if model.startswith("nano-banana"):
            endpoint = f"{base}/v1/draw/nano-banana"
            # В теле передаём запрошенную модель (nano-banana-pro или nano-banana) — API может поддерживать вариант pro
            data = {
                "model": model,
                "prompt": prompt,
                "urls": urls,
                "shutProgress": True,
            }
            if size and size != "1024x1024":
                data["size"] = size
        else:
            endpoint = f"{base}/v1/draw/completions"
            data = {
                "model": model,
                "prompt": prompt,
                "size": size,
                "urls": urls,
            }
        try:
            response = self.session.post(endpoint, json=data, timeout=120)
            response.encoding = "utf-8"
            response.raise_for_status()
            text = response.text or ""

            # API может вернуть SSE-поток: строки "data: {...}"
            result = None
            if "data: " in text:
                chunk_with_url = None
                for line in text.splitlines():
                    line = line.strip()
                    if line.startswith("data: "):
                        try:
                            chunk = json.loads(line[6:])
                            result = chunk
                            data = chunk.get("data")
                            out = (chunk.get("output") or {}) if isinstance(chunk.get("output"), dict) else {}
                            data_out = (data.get("output") or {}) if isinstance(data, dict) else {}
                            results = chunk.get("results") or []
                            data_list = chunk.get("data") if isinstance(chunk.get("data"), list) else []
                            url_in = (
                                (data.get("url") if isinstance(data, dict) else None)
                                or (data_out.get("url") if isinstance(data_out, dict) else None)
                                or (out.get("url") if out else None)
                                or chunk.get("url")
                                or (results[0].get("url") if results and isinstance(results[0], dict) else None)
                                or (data_list[0].get("url") if data_list and isinstance(data_list[0], dict) else None)
                            )
                            if url_in:
                                chunk_with_url = chunk
                                break
                            if chunk.get("status") in ("completed", "success", "succeeded"):
                                break
                        except (ValueError, KeyError, IndexError):
                            continue
                if chunk_with_url is not None:
                    result = chunk_with_url
            else:
                try:
                    result = response.json()
                except ValueError:
                    pass

            if result is None:
                try:
                    result = json.loads(text)
                except ValueError:
                    logger.warning("Draw API response is not JSON. Status=%s, body[:500]=%s", response.status_code, text[:500])
                    return {"success": False, "error": f"API returned non-JSON (status={response.status_code}). Maybe 'urls' with data URL not supported — try public image URL."}

            if result.get("code") is not None and result.get("code") != 0:
                raise Exception(result.get("msg", "Unknown error"))
            if result.get("status") == "failed":
                err = result.get("error") or result.get("failure_reason") or result.get("msg") or "Generation failed"
                return {"success": False, "error": err}
            # Ответ: url или data (в т.ч. из SSE-чанка; nano-banana может вернуть results[0].url)
            data_obj = result.get("data") if isinstance(result.get("data"), dict) else {}
            out_data = data_obj.get("output")
            out_top = result.get("output")
            results_list = result.get("results") if isinstance(result.get("results"), list) else []
            # data может быть списком: data: [{ url: "..." }]
            data_list = result.get("data") if isinstance(result.get("data"), list) else []
            url = (
                (results_list[0].get("url") if results_list and isinstance(results_list[0], dict) else None)
                or (data_list[0].get("url") if data_list and isinstance(data_list[0], dict) else None)
                or data_obj.get("url")
                or (out_data.get("url") if isinstance(out_data, dict) else None)
                or (out_top.get("url") if isinstance(out_top, dict) else None)
                or result.get("url")
            )
            if url:
                return {"success": True, "url": url}
            # base64
            b64 = (
                (data_list[0].get("b64_json") or data_list[0].get("image") if data_list and isinstance(data_list[0], dict) else None)
                or data_obj.get("b64_json") or data_obj.get("image")
                or result.get("b64_json") or result.get("image")
            )
            if b64:
                return {"success": True, "b64_json": b64}
            # Рекурсивный поиск url / b64 в любом вложении (на случай нового формата API)
            def _find_url_or_b64(obj, depth=0):
                if depth > 10:
                    return None, None
                if isinstance(obj, dict):
                    u = obj.get("url") or obj.get("image_url")
                    if u and isinstance(u, str) and u.startswith(("http", "data:")):
                        return u, None
                    b = obj.get("b64_json") or obj.get("image")
                    if b:
                        return None, b
                    for v in obj.values():
                        u, b = _find_url_or_b64(v, depth + 1)
                        if u or b:
                            return u, b
                elif isinstance(obj, list):
                    for v in obj:
                        u, b = _find_url_or_b64(v, depth + 1)
                        if u or b:
                            return u, b
                return None, None
            url, b64 = _find_url_or_b64(result)
            if url:
                return {"success": True, "url": url}
            if b64:
                return {"success": True, "b64_json": b64}
            # Если это SSE и статус running — возможно, нужен повторный запрос по id (polling)
            if result.get("status") == "running" and result.get("id"):
                logger.info("Draw task is still running, id=%s. Consider polling /v1/draw/result?", result.get("id"))
            logger.warning("Draw API: no image in response. Keys: %s", list(result.keys()) if isinstance(result, dict) else type(result).__name__)
            return {"success": False, "error": "No image in response"}
        except Exception as e:
            logger.exception("Image generation failed: %s", e)
            return {"success": False, "error": str(e)}


# Пример использования
if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    
    # Создание клиента
    client = GRSAIClient()
    
    # Простой запрос
    print("=== Простой запрос ===")
    response = client.simple_ask("Привет! Как дела?")
    print(response)
    
    # Запрос с системным промптом
    print("\n=== Запрос с системным промптом ===")
    response = client.simple_ask(
        question="Напиши короткое стихотворение про Python",
        system_prompt="Ты поэт, который пишет технические стихи"
    )
    print(response)
    
    # Потоковый режим
    print("\n=== Потоковый режим ===")
    for chunk in client.chat_stream(
        messages=[{"role": "user", "content": "Расскажи короткую историю про робота"}]
    ):
        print(chunk, end="", flush=True)
    print()
    
    # Доступные модели
    print("\n=== Доступные модели ===")
    models = GRSAIClient.get_available_models()
    for category, model_list in models.items():
        print(f"{category}: {', '.join(model_list)}")
