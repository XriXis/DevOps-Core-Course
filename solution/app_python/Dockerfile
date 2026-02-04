FROM python:3.14.2-alpine3.23
# OPTIONAL: PORT {5000}, HOST {0.0.0.0}, DEBUG {false}

LABEL authors="xzsay"
RUN apk add --no-cache shadow  \
    && groupadd -r appgroup \
    && useradd -r -g appgroup -m appuser
USER appuser
WORKDIR /app

RUN pip install --upgrade pip>=26.0
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY . .
ENTRYPOINT ["python", "app.py"]
EXPOSE 5000