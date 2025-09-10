FROM python:3.11-slim

#settign working directory
WORKDIR /app

#Install the dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

#copy the requirements and install the python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

#COPY the backend code
COPY . /app/

#create necessary directories
RUN mkdir -p /app/Data /app/VectorDB /app/uploads

#exposing port 
EXPOSE 10000 

#settign env 
ENV FLASK_APP=app.py
ENV FLASK_ENV=development
ENV PYTHONPATH=/app
ENV PORT=10000


#healthcheck 
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:10000/api/health || exit 1

CMD ["python", "app.py"]

