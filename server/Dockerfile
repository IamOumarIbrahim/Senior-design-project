# build from the repo folder: docker build -f server/Dockerfile .
FROM python:3.12-slim
WORKDIR /app/server
COPY server/requirements.txt .
RUN pip install -r requirements.txt
COPY server/ .
COPY dashboard/dist/ ../dashboard/dist/
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
