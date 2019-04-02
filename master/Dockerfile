FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

COPY templates/ ./templates/

RUN python models.py

ENV FLASK_APP master.py

CMD [ "flask", "run", "--host", "0.0.0.0", "--port", "8000" ]
