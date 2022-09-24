FROM alpine
RUN curl -fsSL https://get.docker.com | sh
RUN apk add --no-cache python3 py3-pip
ADD requirements.txt .
RUN pip install -r requirements.txt
ADD main.py .
ADD DockerStack.py .
ADD DockerService.py .
ADD utils.py .
COPY ./stacks-copy ./stacks-copy
CMD ["python3", "./main.py", "--stacks", "./stacks-copy"]