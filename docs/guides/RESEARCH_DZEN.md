# Исследование веб-интерфейса Яндекс.Дзен

Краткая справка. **Полные ответы на все вопросы промпта** (1.1 и 1.2) — в [RESEARCH_DZEN_FULL.md](RESEARCH_DZEN_FULL.md).

Исследование через MCP browser tools и скрипт `docs/scripts/scripts/research_zen_studio.py` (с cookies). Используется для автопостинга по [PLAYWRIGHT_AUTOPOST.md](PLAYWRIGHT_AUTOPOST.md).

**Как исследовать с куки:** `python docs/scripts/scripts/research_zen_studio.py [--editor]` — откроет студию, с `--editor` перейдёт в Публикации.

---

## Вход (авторизация)

### URL
- **Страница студии / редактора:** `https://dzen.ru/profile/editor/flowcabinet` → редирект на `https://dzen.ru/flowcabinet`
- **Логин (Яндекс):** `https://passport.yandex.ru/auth?retpath=https%3A%2F%2Fdzen.ru%2Fprofile%2Feditor%2Fflowcabinet`

### Поля формы

**Вариант 1 — телефон (по умолчанию):**
- `textbox` name: `phone`, value: `+7`, placeholder: `(000) 000-00-00`
- Кнопка «Log in» / «Продолжить»

**Вариант 2 — логин/пароль (через «More» → «Log in with username»):**
- `textbox` name: `Username or email`, placeholder: `Username or email`
- После ввода логина — следующий шаг с полем пароля
- Кнопка «Log in»

**Доп. опции на странице логина:**
- Face or fingerprint login
- QR code
- More → Create an ID for yourself / Create an ID for a child / **Log in with username**

### 2FA, CAPTCHA
- **Капча:** при срабатывании — текст «Вы не робот»; в `zen_client.py` реализовано ожидание 90 сек для ручного решения
- **2FA:** возможна при включённой двухфакторной аутентификации в аккаунте

### Cookies
- Сессия сохраняется в `zen_storage_state.json` через `context.storage_state()`
- Рекомендуется `capture_cookies.py` для первичного сохранения

---

## Студия Дзена (после входа по cookies)

### URL
- `https://dzen.ru/profile/editor/flowcabinet` → редирект на `https://dzen.ru/flowcabinet`
- Title страницы: **«Дзен-студия»**

### Левое меню
- Главная (выбрана)
- Статистика
- Подписчики
- **Публикации** — переход к созданию/списку статей
- Комментарии
- Монетизация
- Донаты
- Настройки
- Всё о Дзене
- Справка
- Поддержка

### Модалки (закрывать до работы)
1. **«Яндекс станет основным поиском»** — `dismiss_yandex_default_search_modal()` из `playwright_helpers.py`
2. **«У нас появились донаты!»** — кнопка «Узнать больше» или крестик; нужно закрыть, чтобы получить доступ к контенту

### Главная студии
- Блок «Важное» (приветствие, новости)
- «С чего начать» (чеклист)
- Показатели статистики
- Последние комментарии
- Последние публикации (ссылки на статьи)

### Создание поста
- Детали редактора см. в `blocks/autopost_zen/zen_client.py` — переход в «Публикации», заполнение заголовка, контента, обложки, тегов

---

## Сеть
- Публикация через API — см. `zen_client.py`, использование `context.request` для обхода CORS

---

## Селекторы (accessibility / ARIA)
| Элемент            | Роль    | Имя / атрибут                          |
|--------------------|---------|----------------------------------------|
| Войти              | button  | name: "Войти"                          |
| Телефон            | textbox | name: "phone"                          |
| Username/email     | textbox | name: "Username or email"              |
| Log in             | button  | name: "Log in"                         |
| More → Log in with username | menuitem | name: "Log in with username" |
