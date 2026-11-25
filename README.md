# Домашняя работа №3. Вариант 13

Программа читает конфигурацию из `stdin` и выдаёт XML в `stdout`. Разбор
синтаксиса выполняет Lark. Если в конфигурации ошибка, программа пишет
сообщение в `stderr` и по возможности указывает строку и столбец.

## Как запустить

Нужен Python 3.10 или новее. Из папки проекта создайте окружение и установите
зависимости.

```bat
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

В командной строке Windows (`cmd.exe`) эта команда покажет XML в консоли.

```bat
run.bat < examples\web_service.cfg
```

Чтобы записать XML в файл и посмотреть его, выполните эти две команды.

```bat
run.bat < examples\web_service.cfg > result.xml
notepad result.xml
```

Для запуска напрямую через Python вместо `run.bat` используйте модуль `src`.

```bat
.\.venv\Scripts\python.exe -m src < examples\web_service.cfg
```

В PowerShell запуск с перенаправлением выглядит так.

```powershell
cmd /d /c 'run.bat < examples\web_service.cfg'
```

На Linux и macOS команды для установки и запуска такие.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m src < examples/web_service.cfg > result.xml
```

Отдельная сборка не нужна. Команды для проверки исходников и запуска тестов
в PowerShell.

```powershell
.\.venv\Scripts\python.exe -m compileall -q src
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

На Linux и macOS замените путь к Python на `.venv/bin/python`.
Справка доступна по ключу `--help`. Конфигурация и XML используют UTF-8.

## Синтаксис

- `#= комментарий =#` может занимать несколько строк.
- `2.` и `0.25` — числа. В аргументах выражений можно писать `2` без точки.
- `q(Привет)` — строка. Она заканчивается на первой `)` и сохраняет
  пробелы и переносы.
- `([ name : значение, ])` — словарь. Значением может быть число, строка,
  другой словарь или результат выражения. Последняя запятая необязательна.
- Имена ключей и констант состоят из строчных латинских букв и `_`.
  Ключи в одном словаре и имена констант нельзя повторять.
- `var base := 2.5;` объявляет константу. Её можно использовать в следующих
  выражениях. После объявлений можно записать одно корневое значение.

Выражения можно вкладывать друг в друга. Операция идёт перед аргументами.

- `|+ a b|` складывает два числа.
- `|- a b|` вычитает `b` из `a`.
- `|pow a b|` возводит `a` в степень `b`.
- `|print a|` возвращает `a` и при успешном запуске печатает его в `stderr`.
  Словари печатаются как фрагменты XML.

[Полная грамматика](src/config.lark)

## Пример

```text
var base := 2.5;
([timeout : |+ base 1|])
```

```xml
<?xml version='1.0' encoding='utf-8'?>
<config>
  <dict>
    <entry name="timeout">
      <number>3.5</number>
    </entry>
  </dict>
</config>
```

### Готовые конфигурации

- [Веб-сервис](examples/web_service.cfg) — адрес, порт и тайм-ауты.
- [Оранжерея](examples/greenhouse.cfg) — температура, влажность и опрос датчиков.
- [Библиотека](examples/library.cfg) — сроки выдачи и лимиты для читателей.
