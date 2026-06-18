FROM python:3.11

WORKDIR /app

# dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# código
COPY . .

# arranque
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]