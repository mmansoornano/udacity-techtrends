FROM python:3.7
LABEL maintainer="Mian Mansooor"

WORKDIR /app
COPY ./project/techtrends/requirements.txt /app

RUN pip install -r requirements.txt
EXPOSE 3111
COPY ./project/techtrends/ /app
RUN python /app/init_db.py

CMD [ "python", "/app/app.py" ]
