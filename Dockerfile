FROM alpine
RUN apk add --no-cache python3 py3-pip docker-cli
ADD requirements.txt .
RUN pip install -r requirements.txt
ADD main.py .
COPY ./src ./src
COPY ./repos ./repos
ADD utils.py .
ADD defaults.yaml .
CMD ["python3", "./main.py"]
