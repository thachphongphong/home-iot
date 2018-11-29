FROM python:3.6-alpine

RUN mkdir -p /home/iot
WORKDIR /home/iot
COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . /home/iot
VOLUME ["/home/iot"]

CMD ["python", "app.py"]