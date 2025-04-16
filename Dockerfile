FROM python:3.10-slim

WORKDIR /app

# 安裝系統依賴（為了支持 pillow、pyautogui、PyGetWindow 等）
RUN apt-get update && apt-get install -y \
    gcc g++ libglib2.0-0 libsm6 libxext6 libxrender-dev \
    libffi-dev libssl-dev curl unzip \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt 並安裝依賴（prefer-binary 加速）
COPY requirements.txt requirements.txt
RUN pip install --prefer-binary --timeout=60 -r requirements.txt

# 複製整個專案目錄進容器
COPY . .

# 指定入口
CMD ["python3", "main.py"]
