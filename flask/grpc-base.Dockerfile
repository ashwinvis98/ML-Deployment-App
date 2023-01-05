# INSTALLS COMPONENTS ALL GRPC SERVERS WILL NEED TO AVOID
# EXCESSIVE BUILD TIMES

# Cloud Build Instructions:
# 1. Install the Google Cloud CLI on your machine and set
#    your project id as ml-deployment-app-370904
# 2. Run the following command from the grpc folder:
#    gcloud builds submit --region=us-central1 --config=grpc-base-cloudbuild.yaml

# Local Build Instructions
# 1. docker build -t ml-deployment-grpc-base:dev -f grpc-base.Dockerfile .


# Inherit from Google Cloud CLI image
FROM gcr.io/google.com/cloudsdktool/google-cloud-cli:latest

# Install dependencies
RUN apt-get update && apt-get upgrade -y \
 && pip install protobuf==3.19.6 numpy grpcio pymysql tensorflow==2.10.1

# Unfuck Tensorflow installation of Protobuf
RUN apt-get install -y wget \
 && wget https://raw.githubusercontent.com/protocolbuffers/protobuf/main/python/google/protobuf/internal/builder.py \
    -O /usr/local/lib/python3.9/dist-packages/google/protobuf/internal/builder.py