FROM tiangolo/uwsgi-nginx-flask:python3.7

RUN mkdir /gfr
COPY ./Lib /gfr/Lib
COPY ./setup.py /gfr/setup.py
RUN pip install /gfr

COPY ./entrypoint.sh /entrypoint.sh
COPY ./app /app

RUN chmod +x /entrypoint.sh
