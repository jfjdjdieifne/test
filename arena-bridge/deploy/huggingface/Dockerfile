# Hugging Face Docker Space — ملف Space (نسخة مع chromium لمحاكاة المتصفح)
# بناء أول مرة ياخد ~3-5 دقائق. مساحة القرص كافية بالخطة المجانية.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PORT=7860 \
    HOST=0.0.0.0

RUN apt-get update && apt-get install -y --no-install-recommends \
        chromium ca-certificates fonts-liberation ffmpeg \
        libnss3 libatk-bridge2.0-0 libgtk-3-0 libgbm1 libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bridge.py .

EXPOSE 7860

CMD ["uvicorn", "bridge:app", "--host", "0.0.0.0", "--port", "7860"]
