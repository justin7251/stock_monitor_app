FROM python:3.9-slim

WORKDIR /app

# Install MySQL client
RUN apt-get update && apt-get install -y default-libmysqlclient-dev gcc


# Copy requirements and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
