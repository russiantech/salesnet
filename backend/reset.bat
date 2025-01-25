REM delete database /q: quiet mode, do not prompt for confirmation
del /q app.db
REM remove migrations folder
rd /q /s migrations

REM remove __pychache__ folder
rd /q /s __pychache__

flask db init && flask db migrate && flask db upgrade