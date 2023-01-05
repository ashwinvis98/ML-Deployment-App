import os
import subprocess
import time
import pprint
import sys
# import google.auth
# from google.cloud.devtools import cloudbuild_v1

pp = pprint.PrettyPrinter(indent=1)

def get_service_info() -> dict:
    """
    Returns the output of "kubectl get services --sort-by=.metadata.creationTimestamp"
    formatted as such:
    {
        'service-1-name': {
            'TYPE': 'LoadBalancer', 
            'CLUSTER-IP': '10.0.0.0',
            'EXTERNAL-IP': '34.23.323.31',
            'PORT(S)': '5000:30547/TCP',
            'AGE': '5m42s'
        }
    }
    """
    
    # List current pods running
    result = subprocess.run(
        "kubectl get services --sort-by=.metadata.creationTimestamp",
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        universal_newlines = True,
        shell = True
    ).stdout

    # Format the kubectl output 
    svc_arr = result.split()
    n_services = (len(svc_arr) // 6) - 1
    
    if n_services == 0:
        return None

    svc_info = {}
    for svc_idx in range(1, n_services + 1):
        curr_svc_info = {}
        curr_svc_idx = svc_idx*6
        curr_svc_name = svc_arr[curr_svc_idx]

        curr_svc_info['TYPE'] = svc_arr[curr_svc_idx+1]
        curr_svc_info['CLUSTER-IP'] = svc_arr[curr_svc_idx+2]
        curr_svc_info['EXTERNAL-IP'] = svc_arr[curr_svc_idx+3]
        curr_svc_info['PORT(S)'] = svc_arr[curr_svc_idx+4]
        curr_svc_info['AGE'] = svc_arr[curr_svc_idx+5]

        svc_info[curr_svc_name] = curr_svc_info
    
    return svc_info

def get_pod_info() -> dict:
    """
    Returns the output of "kubectl get pods --sort-by=.metadata.creationTimestamp"
    formatted as such:
    {
        'model-1-name': {
            'READY': '1/1', 
            'STATUS': 'Running',
            'RESTARTS': '0',
            'AGE': '5m42s'
        }
    }
    """
    
    # List current pods running
    result = subprocess.run(
        "kubectl get pods --sort-by=.metadata.creationTimestamp",
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        universal_newlines = True,
        shell = True
    ).stdout

    # Format the kubectl output 
    pod_arr = result.split()
    n_pods = (len(pod_arr) // 5) - 1
    
    if n_pods == 0:
        return None

    pod_info = {}
    for pod_idx in range(1, n_pods + 1):
        curr_pod_info = {}
        curr_pod_idx = pod_idx*5
        curr_pod_name = pod_arr[curr_pod_idx]

        curr_pod_info['READY'] = pod_arr[curr_pod_idx+1]
        curr_pod_info['STATUS'] = pod_arr[curr_pod_idx+2]
        curr_pod_info['RESTARTS'] = pod_arr[curr_pod_idx+3]
        curr_pod_info['AGE'] = pod_arr[curr_pod_idx+4]

        pod_info[curr_pod_name] = curr_pod_info
    
    return pod_info

def get_status_by_name(model_name, object_type):
    """
    Takes the output from get_pod_info() or get_service_info()
    and returns the status of the object whose name contains
    model_name.
    """
    # Get the info for the corresponding object type
    if object_type == 'pod':
        info = get_pod_info()
    elif object_type == 'service':
        info = get_service_info()
        pp.pprint(info)
    else:
        print("Invalid Kubernetes object type supplied.")
        return None
    
    # Get the status of the specified object
    for object in list(info.keys()):
        if model_name in object:
            return info[object]
        
    # Could not find object
    print("Could not find object specified.")
    return None


def wait_for_deployment(model_name):
    """
    Waits until the most recent deployed pod is either running
    or in a state where it is guaranteed not to run. Return the
    status of the pod and it's public IP, if it succeeds in running.
    """
    time.sleep(5)
    pod_status, service_ip = '', ''
    pod_statuses = ['Running', 'CrashLoopBackOff', 'ImagePullBackOff', 'ErrImagePull', 'Terminated']
    service_ip_statuses = ['<none>', '<pending>', '']
    
    # Wait for the pod to be deployed
    while pod_status not in pod_statuses:
        print("pod status:", pod_status)
        pod_info = get_status_by_name(model_name, 'pod')
        pod_status = pod_info['STATUS']
        time.sleep(2)

    print("Pod status after loop:", pod_status)

    # Get service IP address
    if pod_status == 'Running':
        while service_ip in service_ip_statuses:
            print("service ip:", service_ip)
            service_info = get_status_by_name(model_name, 'service')
            service_ip = service_info['EXTERNAL-IP']
            time.sleep(2)

    return pod_status, service_ip


if __name__ == "__main__":
    method = sys.argv[1]

    model_bucket, model_name = 'gs://test-deployments/test-deployment-1/new-test-model/', 'new-test-model'
    data_bucket = 'gs://test-deployments/test-deployment-1/train.json'
    image_repo = 'us-central1-docker.pkg.dev/ml-deployment-app-370904/ml-deployment-repo/ml-deployment-grpc'

    model_bucket_escaped = model_bucket.replace('/', '\/')
    data_bucket_escaped = data_bucket.replace('/', '\/')

    # Change grpc-cloudbuild.yaml and grpc-deployment.yaml to use specified model
    os.system(f"sed -i '' 's/model_name/{model_name}/g' grpc-deployment.yaml grpc-cloudbuild.yaml")
    os.system(f"sed -i '' 's/model_bucket/{model_bucket_escaped}/g' grpc-cloudbuild.yaml")
    os.system(f"sed -i '' 's/data_bucket/{data_bucket_escaped}/g' grpc-cloudbuild.yaml")

    # Run the gcloud command to build and push the model to artifact registry
    # os.system("gcloud builds submit --region=us-central1 --config=grpc-cloudbuild.yaml")

    # # Deploy the model on the K8S cluster
    if method == 'a':
        os.system("kubectl apply -f grpc-deployment.yaml")
        pod_status, service_ip = wait_for_deployment(model_name)
        print(f"pod status: {pod_status}, service_ip: {service_ip}")
    elif method == 'd':
        os.system("kubectl delete -f grpc-deployment.yaml")

    # # Change the config files back to their template form
    os.system(f"sed -i '' 's/{data_bucket_escaped}/data_bucket/g' grpc-cloudbuild.yaml")
    os.system(f"sed -i '' 's/{model_bucket_escaped}/model_bucket/g' grpc-cloudbuild.yaml")
    os.system(f"sed -i '' 's/{model_name}/model_name/g' grpc-deployment.yaml grpc-cloudbuild.yaml")

# Authorize the client with Google defaults
# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'flask-creds.json'
# credentials, project_id = google.auth.default()

# client = cloudbuild_v1.services.cloud_build.CloudBuildClient()

# build = cloudbuild_v1.Build()
# build.steps = [
#     {"name": "gcr.io/cloud-builders/docker",
#     "args": [
#         'build',
#         '--build-arg', f'MODEL_NAME={model_name}',
#         '--build-arg', f'MODEL_BUCKET={storage_bucket}',
#         '-f', 'grpc.Dockerfile',
#         '-t', f'{image_repo}:{model_name}', '.'
#     ]}
# ]
# build.images = [f'{image_repo}:{model_name}']

# operation = client.create_build(project_id=project_id, build=build)
# # Print the in-progress operation
# print("IN PROGRESS:")
# print(operation.metadata)

# result = operation.result()
# # Print the completed status
# print("RESULT:", result.status)