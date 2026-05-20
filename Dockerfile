FROM python:3.11-alpine

# Alpine లో సిస్టమ్ అప్‌డేట్ మరియు క్లీన్ అప్
RUN apk update && apk upgrade && rm -rf /var/cache/apk/*

WORKDIR /app

# 1. ముందస్తుగా pip, setuptools మరియు wheel ని అప్‌గ్రేడ్ చేయండి
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# requirements కాపీ చేసి ఇన్‌స్టాల్ చేయండి
COPY requirements.txt .

# 2. Binary ఫైల్స్ మాత్రమే వాడమని ఫోర్స్ చేస్తూ ఇన్‌స్టాల్ చేయండి
RUN pip install --no-cache-dir --only-binary=:all: -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
