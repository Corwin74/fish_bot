## Продаём рыбу в Telegram

Это Telegram-бот для продажи рыбы.

Для запуска вам понадобится:
Python 3.6 или выше
Магазин с товарами в Elastic Path. 
Необходимо зарегистрировать бота и получить токен для доступа к API Телеграма. 
    
## Как установить
Для начала работы необходимо:
- Скопировать репозиторий к себе на компьютер:
```
git clone git@github.com:Corwin74/https://github.com/Corwin74/fish_bot.git
```
Сгенерируйте ключ приложения (Application Key) в Elastic Path. Для этого перейдите Settings → Application Keys и нажмите Create. Имя ключа может быть любое. Сохраните CLIENT_ID и CLIENT_SECRET, они понадобятся для получения токена к API Elastic Path.
Далее, в корневой папке проекта необходимо создать файл `.env` и записать в него настройки в виде:
```
TLGM_TOKEN_BOT=<токен для бота, полученный от BotFather>
ADMIN_TLGM_CHAT_ID=<id пользователя в Телеграмм, которому будут отправляться уведомления о работе ботов>
MOTLIN_CLIENT_ID=<полученный ранее CLIENT_ID>
MOTLIN_CLIENT_SECRET_KEY=<Полученный ранее CLIENT_SECRET>
```
Затем используйте `pip` для установки зависимостей. Рекомендуется использовать отдельное виртуальное окружение.  
[Инструкция по установке виртуального окружения](https://dvmn.org/encyclopedia/pip/pip_virtualenv/)

```
pip install -r requirements.txt
```
## Запуск и использование
Для запуска бота необходимо ввести команду:
```sh
python fish_tlgm_bot.py
```
Оба бота начинают работу по команде /start и заканчивают по команде /cancel
## Deploy на VPS под Linux
Необходимо на VPS выполнить все шаги описанные выше.  
Для того чтобы запускать нашего бота при старте системы автоматически, воспользуемся системным менеджером `systemd`.
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
Description=Fish telegram bot
After=syslog.target
After=network.target

[Service]
Type=simple
#Пользователя user заменить на актуального
User=user
# замените на свой путь к каталогу, где находится `fish_tlgm_bot.py`
WorkingDirectory=/home/user/fish_bot/
# замените на свои пути к виртуальному окружению и папке с ботом
ExecStart=/home/envs/tlgm_env/bin/python3 /home/user/fish_bot/fish_tlgm_bot.py
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
