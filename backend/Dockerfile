FROM sugoi-app:base

WORKDIR /app

# Adicionar binarios C/C++ de sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    p7zip-full unrar libreoffice-nogui libmagic1 poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts
COPY pytest.ini ./

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
