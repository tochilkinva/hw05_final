# hw05_final

Tutorial project for creating a site with posts, comments and subscribers in Django.

На сайте можно публиковать посты и оставлять комментарии, поддерживается авторизация пользователей.

### Технологии
Python 3.7, Django 2.2.6

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/tochilkinva/hw05_final.git
```

```
cd hw05_final
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

```
source env/Scripts/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект из папки с manage.py:

```
python3 manage.py runserver
```

### Автор
Валентин
