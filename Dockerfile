FROM python:3.10-slim

WORKDIR /

RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT ["python"]

CMD ["wsgi.py"]