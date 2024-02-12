FROM python:3.11-slim-buster

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip

COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . /usr/src/app/

CMD ["gunicorn", "--bind", "0.0.0.0:80", "wts_infinite_myaile:app"]
