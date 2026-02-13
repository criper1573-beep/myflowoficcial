# Тёмная тема (CSS)

Краткое описание набора CSS-переменных для тёмной темы. Можно скопировать в любой проект.

## Переменные

| Переменная | Назначение |
|------------|------------|
| `--bg` | Фон страницы |
| `--bg-elevated` | Фон карточек, панелей |
| `--text` | Основной текст |
| `--text-muted` | Второстепенный текст |
| `--border` | Границы |
| `--accent` | Акцент (кнопки, ссылки) |
| `--accent-hover` | Акцент при наведении |

## CSS (скопировать в проект)

```css
:root {
  --bg: #1a1a1a;
  --bg-elevated: #252525;
  --text: #e8e8e8;
  --text-muted: #9ca3af;
  --border: #3a3a3a;
  --accent: #3b82f6;
  --accent-hover: #2563eb;
}

body {
  background-color: var(--bg);
  color: var(--text);
}

/* Опционально: карточки, панели */
.card, .panel {
  background-color: var(--bg-elevated);
  border: 1px solid var(--border);
}

a, .btn-primary {
  color: var(--accent);
}
a:hover, .btn-primary:hover {
  color: var(--accent-hover);
}

.secondary, .muted {
  color: var(--text-muted);
}
```

## Использование

1. Подключить стили или вставить блок `:root` + нужные правила в свой CSS.
2. В разметке использовать классы или ссылаться на переменные: `color: var(--text);`.
3. При необходимости переопределить переменные в своём `:root` для кастомизации.

## Медиа-запрос (опционально)

Если нужна автоматическая тёмная тема по системной настройке:

```css
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #1a1a1a;
    --bg-elevated: #252525;
    --text: #e8e8e8;
    --text-muted: #9ca3af;
    --border: #3a3a3a;
    --accent: #3b82f6;
    --accent-hover: #2563eb;
  }
}
```

Тогда в `:root` по умолчанию задайте светлую тему, а тёмная включится при `prefers-color-scheme: dark`.
