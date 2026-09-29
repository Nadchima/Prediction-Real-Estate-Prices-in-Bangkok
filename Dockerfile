# Use the slim Python image to keep the container small.
FROM python:3.12-slim

# Set the working directory inside the container.
WORKDIR /app

# Copy the API and serialized model.
COPY app.py .
COPY models /app/models

# Copy the static web interface.
COPY frontend /app/frontend

# Install pinned dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Expose the FastAPI port.
EXPOSE 8501

# Start the application.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8501"]
