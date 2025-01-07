FROM python:3.13-slim

RUN mkdir /monitor  
WORKDIR /monitor  
ADD . /monitor/

RUN pip install -r requirements.txt

CMD ["python", "main.py"]
