FROM python:3.11

WORKDIR /backend

# dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# código
COPY . .

# arranque
CMD ["uvicorn", "backend.main:backend", "--host", "0.0.0.0", "--port", "8000"]