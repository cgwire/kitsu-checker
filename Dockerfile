# syntax=docker/dockerfile:1.3
FROM python:3.11

RUN pip install --no-cache-dir requests==2.28.2

COPY cgwire_checks.py /root/cgwire_checks.py
RUN chmod 555 /root/cgwire_checks.py

CMD ["/root/cgwire_checks.py"]
