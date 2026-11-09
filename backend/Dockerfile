FROM python:3.14-slim
RUN apt-get update && apt-get install -y --no-install-recommends cmake g++ && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend backend
COPY engine engine
COPY scripts scripts
RUN cmake -S engine -B engine/build -DCMAKE_BUILD_TYPE=Release && cmake --build engine/build -j2
ENV PYTHONPATH=/app/backend PI_CORPUS_DIR=/data/corpus PI_INDEX_FILE=/data/index/pi-prefix-4.sqlite PI_ENGINE_BIN=/app/engine/build/pi_search
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
