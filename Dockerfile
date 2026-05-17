# 1. తక్కువ వల్నరబిలిటీస్ ఉండేలా లేటెస్ట్ స్లిమ్ ఇమేజ్ వాడుతున్నాం
FROM python:3.11-slim-bookworm

# 2. అప్లికేషన్ ఫోల్డర్ సెటప్
WORKDIR /app

# 3. Layer Caching కోసం ముందుగా requirements ని కాపీ చేస్తున్నాం
# దీనివల్ల ప్రతిసారీ pip install రన్ అవ్వదు, బిల్డ్ టైమ్ తగ్గుతుంది
COPY requirements.txt .

# 4. అనవసరమైన ఫైల్స్ లేకుండా ఇన్‌స్టాల్ చేయడం
RUN pip install --no-cache-dir -r requirements.txt

# 5. ఇప్పుడు కోడ్‌ని కాపీ చేస్తున్నాం (.dockerignore ఇక్కడ పనిచేస్తుంది)
COPY . .

# 6. అప్లికేషన్ రన్ చేయడం (Port 80 కి మార్చాను, మీ Kubernetes సర్వీస్ 80 మీద ఉంది కాబట్టి)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
