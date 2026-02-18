# Git: ветки main, dev и feature

Схема ветвления для безопасного деплоя и тестирования.

---

## Ветки

| Ветка | Назначение | Деплой |
|-------|------------|--------|
| **main** | Стабильная версия, продакшен | flowimage.ru |
| **dev** | Рабочая ветка, тестирование | dev.flowimage.ru (поддомен) |
| **feature/название** | Эксперименты, новая функциональность | Не деплоится отдельно |

---

## Workflow

### Ежедневная работа

1. Работаешь в `dev`:
   ```bash
   git checkout dev
   git pull origin dev
   # вносишь изменения
   git add .
   git commit -m "feat: описание"
   git push origin dev
   ```
2. Push в `dev` → вебхук деплоит на **dev.flowimage.ru**. Проверяешь на поддомене.
3. Всё ок → мержишь в `main`:
   ```bash
   git checkout main
   git pull origin main
   git merge dev
   git push origin main
   ```
4. Push в `main` → вебхук деплоит на **flowimage.ru** (продакшен).

### Эксперименты (feature-ветки)

```bash
git checkout dev
git pull
git checkout -b feature/название-фичи
# работа...
git add . && git commit -m "feat: ..."
git push origin feature/название-фичи
# создаёшь Pull Request в dev или мержишь локально:
git checkout dev
git merge feature/название-фичи
git push origin dev
```

---

## Зачем это нужно

- **main** всегда стабильный — можно деплоить в любой момент.
- **dev** на поддомене — проверяешь изменения до попадания в продакшен.
- Если что-то сломалось на dev — основной сайт не затронут.
- Можно отложить правки: не мержишь dev → main, пока не готов.

---

## См. также

- [DEPLOY_WEBHOOK.md](DEPLOY_WEBHOOK.md) — как работает вебхук
- [DEPLOY_STAGING.md](DEPLOY_STAGING.md) — настройка staging (поддомен)
