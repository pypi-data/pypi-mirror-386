FROM ubuntu
RUN apt-get -y update
RUN apt-get -y install python3 python3-dev python3-pip python3-venv libev-dev gcc
RUN python3 -V
RUN mkdir py312
WORKDIR /py312
RUN python3 -m venv .
RUN bin/pip install gunicorn uWSGI bjoern cheroot waitress pyruvate
RUN mkdir -p /home/www
COPY src /home/www/wsgi_benchmark
EXPOSE 9808
RUN chown -R www-data:www-data /home/www/wsgi_benchmark
