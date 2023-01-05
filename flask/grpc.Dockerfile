# BUILDS THE CONTAINER THAT IS ACTUALLY RUN TO
# SERVE DEPLOYED MODELS. 

# Cloud Build Instructions:
# 1. Install the Google Cloud CLI on your machine and set
#    your project id as ml-deployment-app-370904
# 2. Run the following command from the grpc folder:
#    gcloud builds submit --region=us-central1 --config=grpc-cloudbuild.yaml

# Local Build Instructions
# 1. docker build -t ml-deployment-grpc:{model_name} -f grpc.Dockerfile .


FROM us-central1-docker.pkg.dev/ml-deployment-app-370904/ml-deployment-repo/ml-deployment-grpc-base:latest
LABEL MAINTAINER="ashwinvis98@gmail.com"

# Copy over relevant files
WORKDIR /srv
COPY *.py ./

# Set variables from host OS
ARG MODEL_BUCKET
ARG DATA_BUCKET
ENV DATA_BUCKET=$DATA_BUCKET
ARG MODEL_NAME
ENV MODEL_NAME=$MODEL_NAME

# Authenticate to Google Cloud CLI to get model & data
# MAY NEED TO SET GCP PROJECT ID TO ACCESS MYSQL INSTANCE
COPY grpc-service-creds.json ./
RUN gcloud auth login --cred-file=grpc-service-creds.json \
 && gsutil cp -r ${MODEL_BUCKET} . \
 && gsutil cp ${DATA_BUCKET} . \
 && rm grpc-service-creds.json

# Start the server
EXPOSE 50051
CMD [ "python3", "PredictServicer.py"]