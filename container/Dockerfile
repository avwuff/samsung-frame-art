FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN apt-get update && apt-get install -y vim
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# CMD [ "python", "./art.py", "--debug" ]
# CMD [ "/bin/sh" ]
#ENTRYPOINT ["tail", "-f", "/dev/null"]
ENTRYPOINT ["/bin/bash", "run.sh"]