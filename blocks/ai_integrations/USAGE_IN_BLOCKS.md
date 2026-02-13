# Использование GRS AI Client в других блоках

Это руководство показывает, как использовать `GRSAIClient` в ваших блоках для генерации контента.

## Базовый паттерн

```python
from Блоки.интеграции_ии import GRSAIClient

class YourBlock:
    def __init__(self):
        # Инициализация AI клиента
        self.ai_client = GRSAIClient()
    
    def execute(self, content_item):
        # Ваша логика с использованием AI
        response = self.ai_client.simple_ask("Ваш промпт")
        
        # Обработка ответа и обновление content_item
        content_item.metadata['ai_response'] = response
        
        return content_item
```

## Примеры реальных блоков

### 1. Блок генерации заголовков

```python
from Блоки.интеграции_ии import GRSAIClient

class TitlesGeneratorBlock:
    """Генерация заголовков для контента"""
    
    def __init__(self, model="gpt-4o-mini", count=5):
        self.ai_client = GRSAIClient()
        self.model = model
        self.count = count
    
    def execute(self, content_item):
        """
        Генерирует несколько вариантов заголовков
        
        Args:
            content_item: ContentItem с заполненным topic
        
        Returns:
            ContentItem с добавленными заголовками в metadata
        """
        prompt = self._build_prompt(content_item)
        
        response = self.ai_client.simple_ask(
            question=prompt,
            system_prompt="Ты профессиональный копирайтер, специализирующийся на создании цепляющих заголовков",
            model=self.model
        )
        
        # Парсинг заголовков из ответа
        titles = self._parse_titles(response)
        
        # Сохранение в metadata
        content_item.metadata['generated_titles'] = titles
        content_item.metadata['titles_model'] = self.model
        
        return content_item
    
    def _build_prompt(self, content_item):
        """Построение промпта для генерации заголовков"""
        return f"""
Тема: {content_item.topic}
Целевая аудитория: {content_item.target_audience or 'широкая аудитория'}
Тон: {content_item.metadata.get('tone', 'нейтральный')}

Сгенерируй {self.count} цепляющих заголовков для статьи.
Требования:
- Заголовки должны быть короткими (до 60 символов)
- Используй эмоциональные триггеры
- Каждый заголовок на новой строке
- Нумеруй заголовки (1., 2., и т.д.)
"""
    
    def _parse_titles(self, response):
        """Парсинг заголовков из ответа AI"""
        lines = response.strip().split('\n')
        titles = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Удаляем нумерацию (1., 2., и т.д.)
            if line[0].isdigit() and '.' in line[:3]:
                line = line.split('.', 1)[1].strip()
            
            # Удаляем кавычки если есть
            line = line.strip('"\'')
            
            if line:
                titles.append(line)
        
        return titles[:self.count]
```

### 2. Блок генерации текста статьи

```python
from Блоки.интеграции_ии import GRSAIClient

class ArticleTextGeneratorBlock:
    """Генерация текста статьи"""
    
    def __init__(self, model="gemini-2.5-pro", min_words=1500):
        self.ai_client = GRSAIClient()
        self.model = model
        self.min_words = min_words
    
    def execute(self, content_item):
        """
        Генерирует полный текст статьи
        
        Args:
            content_item: ContentItem с заполненным topic и выбранным заголовком
        
        Returns:
            ContentItem с добавленным текстом в content['text']
        """
        title = content_item.metadata.get('selected_title', content_item.topic)
        prompt = self._build_prompt(content_item, title)
        
        # Используем потоковый режим для длинного текста
        article_text = ""
        
        print(f"Генерация статьи '{title}'...")
        
        for chunk in self.ai_client.chat_stream(
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            model=self.model
        ):
            article_text += chunk
            # Можно добавить прогресс-бар здесь
        
        # Сохранение результата
        content_item.content['text'] = article_text
        content_item.metadata['text_model'] = self.model
        content_item.metadata['text_word_count'] = len(article_text.split())
        
        print(f"✓ Статья сгенерирована ({len(article_text.split())} слов)")
        
        return content_item
    
    def _get_system_prompt(self):
        """Системный промпт для генерации статей"""
        return """Ты профессиональный автор статей.

Твои статьи:
- Хорошо структурированы (введение, основная часть, заключение)
- Содержат подзаголовки для удобства чтения
- Написаны простым и понятным языком
- Содержат конкретные примеры и факты
- Заканчиваются выводами или призывом к действию

Пиши естественно, избегай клише и штампов."""
    
    def _build_prompt(self, content_item, title):
        """Построение промпта для генерации статьи"""
        return f"""
Заголовок: {title}
Тема: {content_item.topic}
Целевая аудитория: {content_item.target_audience or 'широкая аудитория'}
Желаемая длина: {self.min_words}-{self.min_words + 500} слов

Напиши полноценную статью с:
1. Вводной частью (зацепка, почему это важно)
2. Основной частью с подзаголовками (раскрытие темы)
3. Заключением (выводы, призыв к действию)

Используй конкретные примеры и факты.
"""
```

### 3. Блок генерации хештегов

```python
from Блоки.интеграции_ии import GRSAIClient

class HashtagsGeneratorBlock:
    """Генерация хештегов для контента"""
    
    def __init__(self, model="gpt-4o-mini", count=10):
        self.ai_client = GRSAIClient()
        self.model = model
        self.count = count
    
    def execute(self, content_item):
        """
        Генерирует хештеги на основе контента
        
        Args:
            content_item: ContentItem с заполненным текстом
        
        Returns:
            ContentItem с добавленными хештегами в metadata
        """
        # Берем первые 500 символов текста для контекста
        text_preview = content_item.content.get('text', '')[:500]
        
        prompt = f"""
Тема: {content_item.topic}
Текст статьи (начало): {text_preview}

Сгенерируй {self.count} релевантных хештегов для этого контента.

Требования:
- Хештеги на русском языке
- Без символа # в начале
- Каждый хештег на новой строке
- Хештеги должны быть популярными и релевантными
"""
        
        response = self.ai_client.simple_ask(
            question=prompt,
            system_prompt="Ты специалист по SMM и знаешь, какие хештеги работают лучше всего",
            model=self.model
        )
        
        # Парсинг хештегов
        hashtags = self._parse_hashtags(response)
        
        # Сохранение
        content_item.metadata['hashtags'] = hashtags
        
        return content_item
    
    def _parse_hashtags(self, response):
        """Парсинг хештегов из ответа"""
        lines = response.strip().split('\n')
        hashtags = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Удаляем # если есть
            line = line.lstrip('#')
            
            # Удаляем нумерацию
            if line[0].isdigit() and '.' in line[:3]:
                line = line.split('.', 1)[1].strip()
            
            # Удаляем пробелы (хештеги не должны содержать пробелы)
            line = line.replace(' ', '')
            
            if line:
                hashtags.append(line)
        
        return hashtags[:self.count]
```

### 4. Блок SEO-оптимизации

```python
from Блоки.интеграции_ии import GRSAIClient

class SEOOptimizerBlock:
    """SEO-оптимизация контента"""
    
    def __init__(self, model="gpt-4o-mini"):
        self.ai_client = GRSAIClient()
        self.model = model
    
    def execute(self, content_item):
        """
        Генерирует SEO-метаданные
        
        Args:
            content_item: ContentItem с заполненным текстом
        
        Returns:
            ContentItem с добавленными SEO-данными в metadata
        """
        title = content_item.metadata.get('selected_title', content_item.topic)
        text_preview = content_item.content.get('text', '')[:1000]
        
        prompt = f"""
Заголовок: {title}
Текст статьи (начало): {text_preview}

Создай SEO-оптимизацию для этой статьи:

1. META DESCRIPTION (150-160 символов) - краткое описание для поисковиков
2. KEYWORDS (10-15 ключевых слов через запятую)
3. SEO TITLE (если нужно улучшить текущий заголовок для SEO)

Формат ответа:
META_DESCRIPTION: [текст]
KEYWORDS: [слово1, слово2, ...]
SEO_TITLE: [текст]
"""
        
        response = self.ai_client.simple_ask(
            question=prompt,
            system_prompt="Ты SEO-специалист с опытом оптимизации контента для поисковых систем",
            model=self.model
        )
        
        # Парсинг SEO-данных
        seo_data = self._parse_seo_data(response)
        
        # Сохранение
        content_item.metadata['seo'] = seo_data
        
        return content_item
    
    def _parse_seo_data(self, response):
        """Парсинг SEO-данных из ответа"""
        seo_data = {
            'meta_description': '',
            'keywords': [],
            'seo_title': ''
        }
        
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('META_DESCRIPTION:'):
                seo_data['meta_description'] = line.split(':', 1)[1].strip()
            
            elif line.startswith('KEYWORDS:'):
                keywords_str = line.split(':', 1)[1].strip()
                seo_data['keywords'] = [k.strip() for k in keywords_str.split(',')]
            
            elif line.startswith('SEO_TITLE:'):
                seo_data['seo_title'] = line.split(':', 1)[1].strip()
        
        return seo_data
```

### 5. Блок модерации контента

```python
from Блоки.интеграции_ии import GRSAIClient

class ContentModerationBlock:
    """Модерация и проверка контента"""
    
    def __init__(self, model="gpt-4o-mini"):
        self.ai_client = GRSAIClient()
        self.model = model
    
    def execute(self, content_item):
        """
        Проверяет контент на соответствие правилам
        
        Args:
            content_item: ContentItem с заполненным текстом
        
        Returns:
            ContentItem с результатами модерации в metadata
        """
        text = content_item.content.get('text', '')
        
        prompt = f"""
Проверь следующий текст на:
1. Наличие оскорблений, мата, дискриминации
2. Фактические ошибки или недостоверную информацию
3. Грамматические и орфографические ошибки
4. Общее качество текста

Текст:
{text}

Формат ответа:
ОЦЕНКА: [число от 1 до 10]
ПРОБЛЕМЫ: [список проблем или "нет проблем"]
РЕКОМЕНДАЦИИ: [рекомендации по улучшению]
"""
        
        response = self.ai_client.simple_ask(
            question=prompt,
            system_prompt="Ты модератор контента и редактор с опытом проверки текстов",
            model=self.model
        )
        
        # Парсинг результатов модерации
        moderation_result = self._parse_moderation(response)
        
        # Сохранение
        content_item.metadata['moderation'] = moderation_result
        content_item.metadata['is_approved'] = moderation_result['score'] >= 7
        
        return content_item
    
    def _parse_moderation(self, response):
        """Парсинг результатов модерации"""
        result = {
            'score': 0,
            'issues': [],
            'recommendations': ''
        }
        
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('ОЦЕНКА:'):
                score_str = line.split(':', 1)[1].strip()
                try:
                    result['score'] = int(score_str.split()[0])
                except (ValueError, IndexError):
                    result['score'] = 5
            
            elif line.startswith('ПРОБЛЕМЫ:'):
                issues_str = line.split(':', 1)[1].strip()
                if issues_str.lower() != 'нет проблем':
                    result['issues'] = [issues_str]
            
            elif line.startswith('РЕКОМЕНДАЦИИ:'):
                result['recommendations'] = line.split(':', 1)[1].strip()
        
        return result
```

## Лучшие практики

### 1. Обработка ошибок

Всегда оборачивайте вызовы AI в try-except:

```python
def execute(self, content_item):
    try:
        response = self.ai_client.simple_ask(prompt)
        # обработка ответа
    except Exception as e:
        # Логирование ошибки
        logger.error(f"AI request failed: {e}")
        
        # Установка флага ошибки
        content_item.metadata['ai_error'] = str(e)
        
        # Можно вернуть content_item с ошибкой или пробросить исключение
        return content_item
```

### 2. Логирование

Добавляйте логирование для отладки:

```python
import logging

logger = logging.getLogger(__name__)

def execute(self, content_item):
    logger.info(f"Starting AI generation for topic: {content_item.topic}")
    
    response = self.ai_client.simple_ask(prompt)
    
    logger.info(f"AI response received, length: {len(response)}")
    
    return content_item
```

### 3. Кэширование

Для одинаковых запросов можно использовать кэш:

```python
from functools import lru_cache

class YourBlock:
    @lru_cache(maxsize=100)
    def _get_ai_response(self, prompt_hash):
        """Кэшированный запрос к AI"""
        return self.ai_client.simple_ask(self.prompts[prompt_hash])
```

### 4. Выбор модели

Выбирайте модель в зависимости от задачи:

```python
# Для простых задач (заголовки, хештеги)
model = "gpt-4o-mini"

# Для сложных задач (длинные статьи, анализ)
model = "gemini-2.5-pro"

# Для потокового вывода длинного текста
model = "gemini-2.5-pro"
```

### 5. Промпт-инжиниринг

Создавайте четкие и структурированные промпты:

```python
def _build_prompt(self, content_item):
    """Хороший промпт - структурированный и четкий"""
    return f"""
КОНТЕКСТ:
Тема: {content_item.topic}
Аудитория: {content_item.target_audience}

ЗАДАЧА:
Сгенерируй 5 заголовков для статьи

ТРЕБОВАНИЯ:
1. Длина до 60 символов
2. Используй эмоциональные триггеры
3. Избегай clickbait

ФОРМАТ ОТВЕТА:
1. [заголовок]
2. [заголовок]
...
"""
```

## Тестирование блоков

Создайте тестовый скрипт для вашего блока:

```python
# test_your_block.py
from Блоки.ваш_блок import YourBlock
from core.content_item import ContentItem

def test_block():
    # Создание тестового content_item
    content_item = ContentItem(
        topic="Искусственный интеллект",
        target_audience="разработчики"
    )
    
    # Выполнение блока
    block = YourBlock()
    result = block.execute(content_item)
    
    # Проверка результата
    assert 'generated_titles' in result.metadata
    assert len(result.metadata['generated_titles']) > 0
    
    print("✓ Тест пройден")
    print(f"Результат: {result.metadata['generated_titles']}")

if __name__ == "__main__":
    test_block()
```

## См. также

- [README.md](README.md) — основная документация GRS AI Client
- [grs_ai_client.py](grs_ai_client.py) — исходный код клиента
- [../../GRS_AI_API_INTEGRATION.md](../../GRS_AI_API_INTEGRATION.md) — документация по API
