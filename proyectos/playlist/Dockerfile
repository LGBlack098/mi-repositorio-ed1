FROM python:3.12-slim
WORKDIR /app
COPY requirements-web.txt ./
RUN pip install --no-cache-dir -r requirements-web.txt
COPY main.py ./
COPY models ./models
COPY controllers ./controllers
COPY services ./services
COPY views ./views
COPY assets/sonoteca.ico assets/sonoteca.png ./assets/
ENV SONOTECA_DATA_DIR=/data
VOLUME ["/data"]
EXPOSE 8000
CMD ["python", "main.py", "--web", "--sin-abrir", "--host", "0.0.0.0", "--port", "8000"]
