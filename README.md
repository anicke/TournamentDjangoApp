Set up:

* Copy "/GenericSportTables/DEFAULT_SETTINGS.py" to "/GenericSportTables/LOCAL_SETTINGS.py"
* Make changes to "/GenericSportTables/LOCAL_SETTINGS.py". At least enter enter something in "SECRET_KEY".
* Init database. Run "python manage.py makemigrations sportApp" and "python manage.py migrate".