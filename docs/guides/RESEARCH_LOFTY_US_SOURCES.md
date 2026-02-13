# Поиск по американскому интернету: юрлица и связи Lofty / Kupikod / MyBid

Отчёт о проверке американских источников (реестры компаний, суды, домены, ToS, FTC).

---

## Итог

**Отдельных американских юрлиц** для lofty.today, Kupikod или MyBid **не найдено**. Группа опирается на **UK** (Limited Partnerships, английское право в ToS). В США — только косвенные следы (домен через US privacy proxy, упоминание US-законов в ToS).

---

## 1. Реестры компаний США

| Источник | Результат |
|----------|-----------|
| **Delaware** (Division of Corporations) | Официальный поиск по имени — форма на [icis.corp.delaware.gov](https://icis.corp.delaware.gov/eCorp/EntitySearch/NameSearch.aspx). В веб-поиске **не найдено** записей по "Lofty", "ONEUP", "Arisepeak", "Kupikod" в контексте AdTech/игр. Упоминается только **Lofty.com** (недвижимость, не lofty.today). |
| **California Secretary of State** (bizfile) | Поиск требует ручного ввода в [bizfileonline.sos.ca.gov](https://bizfileonline.sos.ca.gov/search). В открытых обзорах **Lofty/MyBid/Kupikod** не фигурируют. |
| **ONEUP LP / ARISEPEAK LP** | Подтверждённо **UK Limited Partnerships** (Companies House). В US-регистрациях как LP или дочерние структуры **не встречаются**. |

**Вывод:** Американской регистрации под брендами Lofty (lofty.today), Kupikod, MyBid в проверенных реестрах нет.

---

## 2. Юрисдикция и юрлицо в документах

### MyBid (mybid.io)

- **Terms and Conditions** ([mybid.io/terms-and-conditions](https://mybid.io/terms-and-conditions)):
  - **Право и суды:** «Governed by the laws of the UK» / «Laws of England and Wales»; споры — «courts of England», «state or federal courts in London, UK».
  - **Реквизиты компании в конце документа:** поля **Company Name**, **Registration Number**, **Registered Address**, **Phone**, **Email** — **пустые** (не заполнены). Указан только контакт: finance@mybid.io.
- **Вывод:** Оператор MyBid намеренно не раскрывает название юрлица и регистрационные данные в ToS; юрисдикция — Великобритания.

### Kupikod

- Отдельная страница Terms (kupikod.com/terms, kupikod.com/en/terms) по запросу **не открылась** (404/контент не получен).
- В других источниках: приложение в Google Play издаёт **Arisepeak LP** (UK). Юрисдикция в US-источниках не найдена.

---

## 3. Домены и WHOIS

| Домен | Регистратор | Регистрант |
|------|-------------|------------|
| **mybid.io** | GoDaddy.com, LLC | **Privacy:** Domains By Proxy, LLC (Tempe, **Arizona, USA**). Регистрация с 25.02.2021. NS: Cloudflare. |
| **kupikod.com** | В веб-поиске отдельной WHOIS-выдачи не было; типично — privacy или не-US регистрант. |
| **lofty.today** | В поиске не проверялся детально. |

**Вывод:** mybid.io скрыт за американским privacy-прокси (Arizona). Это не свидетельствует о US-юрлице оператора — только о том, что WHOIS скрыт через US-сервис.

---

## 4. Судебные дела (США)

- **Lofty:** Найден только **Lofty, LLC v. McKelly Roofing, LLC** (N.D. Tex., 2017) — спор по контракту/крыше, **не AdTech**, не lofty.today.
- **Kupikod / ONEUP LP / ARISEPEAK LP:** В федеральных делах (Justia, CourtListener, обзоры) **не встречены**.
- **Arisepeak:** В результатах — **Arise Virtual Solutions, Inc.** (трудовая тяжба, Флорида), **не ARISEPEAK LP**.
- **OneUp:** В результатах — **OneUp Trader, LLC** (Иллинойс), **не ONEUP LP** (Kupikod).

**Вывод:** Упоминаний lofty.today, Kupikod, ONEUP LP, ARISEPEAK LP в американской судебной практике по проверенным источникам нет.

---

## 5. FTC, BBB, жалобы

- **FTC:** Отдельных жалоб или решений FTC по Kupikod/Steam/подпискам в поиске **не найдено**.
- **BBB:** По запросу «Kupikod Steam» — общие страницы о подаче жалоб и пример Valve; **профиля или жалоб на Kupikod нет**.

---

## 6. Прочие US-источники

- **SEC:** Нет отождествления Kupikod/ONEUP/Arisepeak с эмитентами или ответчиками в найденных материалах (найденные дела SEC — другие компании).
- **Stripe / PayPal:** Прямых упоминаний lofty.today, mybid.io или kupikod в контексте US-мерчантов в результатах поиска **нет**.

---

## Резюме

| Вопрос | Ответ |
|--------|--------|
| Есть ли US-юрлицо у Lofty/Kupikod/MyBid? | В открытых US-реестрах и судах **не обнаружено**. |
| Где заявлена юрисдикция? | **UK / England and Wales** (MyBid ToS). |
| Кто виден по UK? | ONEUP LP, ARISEPEAK LP (партнёры по LP в реестре не раскрыты). |
| Следы в США? | Домен mybid.io скрыт через US privacy proxy (Arizona); в ToS MyBid — отсылки к US-законам (CAN-SPAM, TCPA и т.д.) для рекламодателей, без указания US-компании оператора. |

Для углубленной проверки США имеет смысл: (1) ручной поиск в Delaware/California/Nevada по названиям и вариациям; (2) поиск в PACER по названиям компаний и доменов; (3) запрос WHOIS/registrar по lofty.today и kupikod.com.

---

*Февраль 2026.*
