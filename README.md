# fish bot
## Чат-боты для проведения викторин
Репозиторий содержит боты для проведения викторин для Телеграмма и социальной сети ВКонтакте.
## Как установить
Для начала работы необходимо:
- Скопировать репозиторий к себе на компьютер:
```
git clone git@github.com:Corwin74/https://github.com/Corwin74/quiz_bot.git
```
Далее, в корневой папке проекта необходимо создать файл `.env` и записать в него настройки в виде:
```
TLGM_TOKEN_BOT=<токен для бота, полученный от BotFather>
ADMIN_TLGM_CHAT_ID=<id пользователя в Телеграмм, которому будут отправляться уведомления о работе ботов>
VK_API_TOKEN=<токен с полномочиями отправлять сообщения в сообщество ВКонтакте>
```
Для работы ботов используется база данных Redis. Для установки по умолчанию необходимо выполнить:
```sh
sudo apt install redis-server
```
Если для ботов будет использоваться конфигурация Redis не по умолчанию (localhost, port=6379, db=0), то необходимо в файле `.env` добавить соответствующие значения:
```
REDIS_HOST=myredis.com
REDIS_PORT=11777
REDIS_DB_ID=5
```
По умолчанию боты ищут файлы с данынми викторины в папке `questions`. Вы можете указать другое расположение, добавив в `.env` файл:
```
QUIZ_DIR=/home/user/data
```
Образец файла с данными для викторины - `example.txt`  
Затем используйте `pip` для установки зависимостей. Рекомендуется использовать отдельное виртуальное окружение.  
[Инструкция по установке виртуального окружения](https://dvmn.org/encyclopedia/pip/pip_virtualenv/)

```
pip install -r requirements.txt
```
## Запуск и использование
Для запуска бота необходимо ввести команду:
```sh
python quiz_tlgm.py
```
или
```sh
python quiz_vk.py
```
Оба бота начинают работу по команде /start и заканчивают по команде /cancel
## Deploy на VPS под Linux
Необходимо на VPS выполнить все шаги описанные выше.  
Для того чтобы запускать нашего бота при старте системы автоматически, воспользуемся системным менеджером `systemd`.
Пример будет показан для бота `quiz_tlgm.py` и названия сервиса `bot.service`. Для второго бота выполнить аналогичные действия, но с другими именами.  
Создадим файл `bot.service` в директории `/etc/systemd/system` :
```
$ sudo touch /etc/systemd/system/bot.service
```
Затем откроем его:
```
$ sudo nano /etc/systemd/system/bot.service
```
и вставим следующее содержимое и сохраняем файл:
```
[Unit]
Description=Quiz telegram bot
After=syslog.target
After=network.target

[Service]
Type=simple
#Пользователя user заменить на актуального
User=user
# замените на свой путь к каталогу, где находится `boltun_tlgm.py`
WorkingDirectory=/home/user/quiz_bot/
# замените на свои пути к виртуальному окружению и папке с ботом
ExecStart=/home/envs/tlgm_env/bin/python3 /home/user/quiz_bot/quiz_tlgm.py
RestartSec=10
Restart=always

[Install]
WantedBy=multi-user.target
```
в консоли выполним:
```
# перечитываем конфигурацию 
# (обнаружит файл `bot.service`)
$ sudo systemctl daemon-reload

# подключаем демон `bot.service`
$ sudo systemctl enable bot

# запускаем демон `bot.service`
$ sudo systemctl start bot

# смотрим статус демона `bot.service`
$ sudo systemctl status bot
```
Теперь перезапустить/остановить телеграмм-бота можно системными командами Linux:
```
# перезапуск
$ sudo systemctl restart bot

# остановка
$ sudo systemctl stop bot

# запуск после остановки
$ sudo systemctl start bot
```
Логи бота можно просмотреть командой:
```
$sudo journalctl -u bot.service
```
## Цель проекта
Код написан в образовательных целях на онлайн-курсе [dvmn.org](https://dvmn.org/).
