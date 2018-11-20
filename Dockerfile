FROM python:3.6-stretch

RUN mkdir -p /home/iot
WORKDIR /home/iot
COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY  boot.sh /boot.sh
RUN chmod +x /boot.sh

COPY . /home/iot
VOLUME ["/home/iot"]

EXPOSE 5000
ENTRYPOINT ["/boot.sh"]