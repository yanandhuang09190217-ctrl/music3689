# 使用 Python 3.11
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統必要套件
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有程式
COPY . .

# 啟動機器人
CMD ["python", "main.py"]
