import predict_pb2
import predict_pb2_grpc
import grpc

import random
import numpy as np
import json

# Configure the stub
channel = grpc.insecure_channel("34.170.133.172:50051")
stub = predict_pb2_grpc.predictStub(channel)

# Configure the data
f = open('prod.json')
prod_data = json.load(f)
col_names = list(prod_data[0].keys())
request = [row[col_name] for col_name in col_names \
            if col_name != 'medv' for row in prod_data]

# Build the PB message
data = predict_pb2.modelInput()
data.X.extend(request)

# # Send the request and print result
resp = stub.Predict(data)
print("Response is:", resp.preds)