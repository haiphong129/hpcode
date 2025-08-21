@echo off
REM ============================
REM Di chuyển đến thư mục chứa file bat
REM ============================
cd /d %~dp0

REM ============================
REM Nếu không có migrations thì cài đặt và khởi tạo DB
REM ============================
if not exist "migrations" (
    echo Khong co thu muc migrations, bat dau cai dat...
    
    echo 1. Cai dat requirements...
    pip install -r requirements.txt

    echo 2. Cai dat Pandoc...
    msiexec /i "app\static\judle\pandoc-3.7.0.2-windows-x86_64.msi" /quiet /norestart

    echo 3. Khoi tao database...
    flask db init
    flask db migrate
    flask db upgrade
) else (
    echo Thu muc migrations da ton tai, bo qua cai dat va khoi tao DB.
)

REM ============================
REM Luon chay waitress server
REM ============================
echo Khoi dong server voi waitress...
start cmd /k "flask run --host 0.0.0.0 --port=80"

REM ============================
REM Lấy địa chỉ IP của máy
REM ============================
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr "IPv4"') do (
    set ip=%%a
    goto :done
)
:done
set ip=%ip: =%

REM ============================
REM In ra địa chỉ IP
REM ============================
echo Dia chi IP cua may la: %ip%

REM ============================
REM Mo trinh duyet web voi IP
REM ============================
start http://%ip%/login
pause
