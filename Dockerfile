FROM python:3.9.13

WORKDIR /app

COPY . .

RUN pip install --upgrade pip \
     && pip install --no-cache-dir -r requirements.txt \
