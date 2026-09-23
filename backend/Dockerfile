FROM python:3.11-slim

WORKDIR /app

# Installs the Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copies every backend file (database.py, models.py, schemas.py, alembic.ini, alembic/)
COPY . .

# Exposes the API port
EXPOSE 8000

# Runs the FastAPI server with Uvicorn listening on every network interface
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

