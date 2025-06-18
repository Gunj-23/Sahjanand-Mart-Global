@echo off
echo Installing Sahjanand Mart...
echo.

REM Install the package in development mode
pip install -e .

echo.
echo Installation complete!
echo.

REM Initialize the database
echo Initializing database...
sahjanand-mart init-db

echo.
echo Creating admin user...
sahjanand-mart create-admin --username admin --password admin123

echo.
echo Starting Sahjanand Mart...
echo The application will open in your browser automatically.
echo.

REM Run the application
sahjanand-mart run --open-browser

pause