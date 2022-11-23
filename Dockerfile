FROM alpine
RUN apk add --no-cache python3 py3-pip docker-cli
ADD requirements.txt .
RUN pip install -r requirements.txt
ADD main.py .
ADD DockerStack.py .
ADD DockerService.py .
COPY ./repos ./repos
ADD utils.py .
CMD ["python3", "./main.py"]
