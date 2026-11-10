FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

RUN addgroup --system app \
    && adduser --system --ingroup app app \
    && chown app:app /app

COPY --chown=app:app . .

USER app

EXPOSE 5000

CMD ["python", "-m", "flask", "--app", "run:app", "run", "--host=0.0.0.0", "--port=5000"]
