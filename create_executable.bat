ECHO OFF

REM DOS Script for creating executables for app.py, client.py, test.py using py2exe 

TITLE create executables

IF EXIST %cd%\dist\NUL rd /s /q %cd%\dist\

ECHO [ creating client exe... ]
IF EXIST %cd%\client\NUL rd /s /q %cd%\client\
python setup_client.py py2exe
rename dist client
copy settings.yml client
ECHO [ done! ]

ECHO [ creating app exe... ]
IF EXIST database.db del /F database.db
python setup_db.py
IF EXIST %cd%\app\NUL rd /s /q %cd%\app\
python setup_app.py py2exe
rename dist app
copy settings.yml app
xcopy templates app\templates\ /E
xcopy static app\static\ /E
move database.db app
ECHO [ done! ]

ECHO [ creating tests exe... ]
IF EXIST %cd%\tests\NUL rd /s /q %cd%\tests\
python setup_tests.py py2exe
rename dist tests
copy settings.yml tests
ECHO [ done! ]

PAUSE
