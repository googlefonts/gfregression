FROM tiangolo/uwsgi-nginx-flask:python3.7

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY ./app /app
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh