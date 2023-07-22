# Парсер pep документации

## Описание
Парсер выполняет следующие функции:
- Собирает ссылки на статьи о нововведениях в Python, переходит по ним и забирает информацию об авторах и редакторах статей.
- Собирает информацию о статусах версий Python.
- Скачивает архив с актуальной документацией.
- Считает статусы документов PEP


### Запуск
Сброр ссылок на статьи о нововведениях в Python:
```bash
python main.py whats-new
```
Сброр информации о версиях Python:
```bash
python main.py latest-versions
```
Скачивание архива с актуальной документацией:
```bash
python main.py download
```
Сброр статусов документов PEP и подсчёт статусов:
```bash
python main.py pep
```

### Аргументы командной строки
Полный список аргументов:
```bash
python main.py -h
```
```bash
usage: main.py [-h] [-c] [-o {pretty,file}] {whats-new,latest-versions,download,pep}

Парсер документации Python

positional arguments:
  {whats-new,latest-versions,download,pep}
                        Режимы работы парсера

options:
  -h, --help            show this help message and exit
  -c, --clear-cache     Очистка кеша
  -o {pretty,file}, --output {pretty,file}
                        Дополнительные способы вывода данных
```
