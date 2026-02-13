"""
Тестовый скрипт для проверки работы GRS AI клиента

Использование (из корня проекта):
    python docs/scripts/scripts/test_grs_ai.py
"""

import sys
import os
import logging
from pathlib import Path

# Корень проекта (3 уровня вверх от папки scripts)
_project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_project_root))

from blocks.ai_integrations import GRSAIClient


def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_simple_ask():
    """Тест простого запроса"""
    print("\n" + "="*60)
    print("ТЕСТ 1: Простой запрос")
    print("="*60)
    
    client = GRSAIClient()
    
    response = client.simple_ask("Привет! Как дела?")
    print(f"\nОтвет: {response}")
    
    return True


def test_with_system_prompt():
    """Тест с системным промптом"""
    print("\n" + "="*60)
    print("ТЕСТ 2: Запрос с системным промптом")
    print("="*60)
    
    client = GRSAIClient()
    
    response = client.simple_ask(
        question="Напиши короткое стихотворение про Python (4 строки)",
        system_prompt="Ты поэт, который пишет технические стихи"
    )
    print(f"\nОтвет:\n{response}")
    
    return True


def test_chat_with_context():
    """Тест диалога с контекстом"""
    print("\n" + "="*60)
    print("ТЕСТ 3: Диалог с контекстом")
    print("="*60)
    
    client = GRSAIClient()
    
    messages = [
        {"role": "system", "content": "Ты помощник по написанию контента"},
        {"role": "user", "content": "Мне нужен заголовок для статьи про искусственный интеллект"},
    ]
    
    response = client.chat(messages=messages, model="gpt-4o-mini")
    print(f"\nОтвет: {response}")
    
    return True


def test_streaming():
    """Тест потокового режима"""
    print("\n" + "="*60)
    print("ТЕСТ 4: Потоковый режим")
    print("="*60)
    
    client = GRSAIClient()
    
    print("\nГенерация текста:")
    print("-" * 60)
    
    for chunk in client.chat_stream(
        messages=[{"role": "user", "content": "Напиши короткую историю про робота (3-4 предложения)"}]
    ):
        print(chunk, end="", flush=True)
    
    print("\n" + "-" * 60)
    
    return True


def test_different_models():
    """Тест разных моделей"""
    print("\n" + "="*60)
    print("ТЕСТ 5: Разные модели")
    print("="*60)
    
    client = GRSAIClient()
    
    models_to_test = ["gpt-4o-mini", "gemini-2.5-flash"]
    question = "Что такое Python? (ответь одним предложением)"
    
    for model in models_to_test:
        print(f"\nМодель: {model}")
        try:
            response = client.simple_ask(question, model=model)
            print(f"Ответ: {response}")
        except Exception as e:
            print(f"Ошибка: {e}")
    
    return True


def test_available_models():
    """Тест получения списка моделей"""
    print("\n" + "="*60)
    print("ТЕСТ 6: Доступные модели")
    print("="*60)
    
    models = GRSAIClient.get_available_models()
    
    for category, model_list in models.items():
        print(f"\n{category.upper()}:")
        for model in model_list:
            print(f"  - {model}")
    
    return True


def test_error_handling():
    """Тест обработки ошибок"""
    print("\n" + "="*60)
    print("ТЕСТ 7: Обработка ошибок (fallback)")
    print("="*60)
    
    client = GRSAIClient()
    
    try:
        # Пробуем с fallback
        response = client.chat(
            messages=[{"role": "user", "content": "Привет!"}],
            model="gpt-4o-mini",
            use_fallback=True
        )
        print(f"\nОтвет получен: {response[:100]}...")
        print("✓ Fallback работает корректно")
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        return False
    
    return True


def main():
    """Основная функция"""
    setup_logging()
    
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ GRS AI CLIENT")
    print("="*60)
    
    # Проверка наличия API ключа
    if not os.getenv("GRS_AI_API_KEY"):
        print("\n⚠️  ВНИМАНИЕ: Переменная окружения GRS_AI_API_KEY не установлена!")
        print("Установите её в .env файле или через export/set")
        print("\nПример:")
        print("  export GRS_AI_API_KEY=your_key  # Linux/Mac")
        print("  set GRS_AI_API_KEY=your_key     # Windows")
        return
    
    tests = [
        ("Простой запрос", test_simple_ask),
        ("Системный промпт", test_with_system_prompt),
        ("Диалог с контекстом", test_chat_with_context),
        ("Потоковый режим", test_streaming),
        ("Разные модели", test_different_models),
        ("Список моделей", test_available_models),
        ("Обработка ошибок", test_error_handling),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n✗ Ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Итоги
    print("\n" + "="*60)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*60)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\nВсего тестов: {total}")
    print(f"Успешно: {passed}")
    print(f"Провалено: {total - passed}")
    
    if passed == total:
        print("\n🎉 Все тесты пройдены!")
    else:
        print(f"\n⚠️  {total - passed} тест(ов) провалено")


if __name__ == "__main__":
    main()
