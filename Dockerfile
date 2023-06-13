# use base from gcr.io/capstone-skincheckai/ml-base
FROM gcr.io/capstone-skincheckai/ml-base

# Allow statements and log messages to immediately appear in the logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME

# Download file model machine learning
RUN curl -o model.h5 https://storage.googleapis.com/public-picture-media-bucket/ml_models/V7_model_mobilenetv2.h5

COPY . ./

# Move the model file to the desired location
RUN mkdir -p /app/models
RUN mv model.h5 /app/models/model.h5

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
# CMD ["python", "app.py"]

CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8080", "app:app"]