# Cloud Build Command:
# gcloud builds submit --region=us-central1 --config=flask-cloudbuild.yaml

# Inherit from Google Cloud CLI image
FROM python:3.8

# Install gcloud CLI
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" \
  | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
 && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg \
  | tee /usr/share/keyrings/cloud.google.gpg && apt-get update -y \
 && apt-get install google-cloud-sdk -y
            

# Configure Google Cloud CLI
WORKDIR /srv
COPY . ./
RUN gcloud auth activate-service-account \
    --key-file=flask-creds.json \
    --project=ml-deployment-app-370904 \
 && rm flask-creds.json \
 && apt-get install kubectl google-cloud-sdk-gke-gcloud-auth-plugin \
 && gcloud container clusters get-credentials ml-deployment-cluster --region=us-central1 --project=ml-deployment-app-370904

# Copy files to start rest server and build gRPC servers

RUN python3 -m pip install --upgrade pip \
 && pip install --upgrade jsonpickle requests flask pymysql numpy

CMD ["python3", "rest-server.py"]