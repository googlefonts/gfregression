FROM tiangolo/uwsgi-nginx-flask:python2.7

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

copy ./app /app
COPY nginx.conf /etc/nginx/conf.d/