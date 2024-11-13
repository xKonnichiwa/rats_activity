GPT Enjoyers. Разметка ЭКоГ
----

### Навигация

- [Исходный код клиента для windows](./backend/app)
- [Инструкция пользователя клиента для windows](./backend/app)
- [Скачать готовый клиент для windows](https://drive.google.com/drive/folders/1SZWEocDi2MWtcWiIJJTnnU7k3wW310GF?usp=sharing)
- [Исходный код Web приложения](./web)
- [Исходный код HTTP сервера](./backend/server)


### Схема трансформации данных

![Схема загружается...](/ml-schema.jpg)

### Структура проекта

| Папка                                          | Описание         |
|:-----------------------------------------------|:-----------------|
| [``./backend``](./backend)                     | Python окружение |
| [``./backend/app/model``](./backend/app/model) | ML модуль        |
| [``./backend/app``](./backend/app)             | Win клиент       |
| [``./backend/server``](./backend/server)       | HTTP Cервер      |
| [``./web``](./web)                             | Веб-интерфейс    |

### Локальный запуск
1. Указать переменные для портов в файл ``.env`` 
```bash
cp .env.example .cp
```
2. Запустить докер сеть
```bash
docker compose -d
```

3. Дождаться установки библиотек внутри контейнеров
4. Перейти в веб-интерфейс по адресу ``http://0.0.0.0:8030``

### Команды для окружения
1. **Web client (SPA)**
```bash
docker compose exec web sh
```
2. **HTTP server (FastAPI)**
```bash
docker compose exec backend bash
```
3. **Window app (PyQt)**
```bash
docker compose exec backend sh -c "cd /project/app && bash"
```

