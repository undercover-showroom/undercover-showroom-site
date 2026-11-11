FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=10000 DATA_ROOT=/var/data
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY assets ./assets
RUN mkdir -p /var/data/uploads /var/data/tickets && chmod 750 /var/data /var/data/uploads /var/data/tickets
EXPOSE 10000
CMD ["python3", "app.py"]
