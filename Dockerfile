FROM python:3.10-slim

WORKDIR /
RUN pip freeze > requirements.txt

COPY . .

ENTRYPOINT ["python"]

CMD ["wsgi.py"]
