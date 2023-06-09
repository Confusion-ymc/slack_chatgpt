FROM python:3.11-slim-bullseye

WORKDIR /code/

RUN pip3 config set global.index-url https://pypi.mirrors.ustc.edu.cn/simple/
RUN pip3 install --upgrade pip

ADD requirements.txt /code/
RUN pip3 install -r requirements.txt

ADD . /code

CMD ["python3", "-u", "main.py"]