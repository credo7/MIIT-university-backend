FROM python:3.9.7

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip \
     && pip install --no-cache-dir -r requirements.txt

COPY . .
