FROM python:3.8-slim AS builder

RUN apt-get update && apt-get install -y python3-pip

COPY requirements.txt ./

RUN pip install --user -r requirements.txt

FROM python:3.8-slim

COPY --from=builder /root/.local /root/.local

COPY . /app

WORKDIR /app

VOLUME [ "/data" ]

CMD ["python", "process_entries.py"]
