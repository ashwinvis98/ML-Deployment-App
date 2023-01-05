# Base Python packages
import base64, io, os, sys, platform, uuid, subprocess, time
# Outside dependencies
from flask import Flask, request, Response, send_file, jsonify
import jsonpickle, pymysql
import numpy as np


app = Flask(__name__)

# import logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.DEBUG)

# PORT = os.getenv("PORT") or "5000"
# HOST = os.getenv("HOST") or "0.0.0.0"
# API_PREFIX = "/ML_Deployment_Service"

# infoKey = "{}.rest.info".format(platform.node())
# debugKey = "{}.rest.debug".format(platform.node())
# errorKey = "{}.rest.error".format(platform.node())

# NOT NEEDED
# def apiCallToObjectStore():
#     return None


def createTable():
    """
    Create the model metadata table in our MySQL server. This includes
    an auto-generate unique ID for the model, the model's name, the 
    public IP of the server running the model, the storage bucket from
    which we got the model, the storage bucket from which we got the model's 
    data, and the time at which the model was deployed.
    """
    # Open database connection
    db = get_db_conn()
    # prepare a cursor object using cursor() method
    cursor = db.cursor()
    # Drop table if it already exist using execute() method.
    cursor.execute("DROP TABLE IF EXISTS model_info")
    # Create table as per requirement
    sql = """
    CREATE TABLE model_info (
    model_id  INT NOT NULL AUTO_INCREMENT,
    model_name  VARCHAR(40) NOT NULL,
    model_public_ip  VARCHAR(40) NOT NULL ,
    model_location  VARCHAR(70) NOT NULL,
    data_location  VARCHAR(70) NOT NULL,
    date  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (model_id))
    """
    cursor.execute(sql)
    print("Table created")
    db.close()

def insertModelInfoToSQL(modelName=None, modelPublicIP=None, modelLocation=None, dataLocation=None):
    # Open database connection
    db = get_db_conn()
    # prepare a cursor object using cursor() method
    cursor = db.cursor() 
    sql = """INSERT INTO model_info(model_name, model_public_ip, model_location, data_location)
    VALUES (%s, %s, %s, %s) """
    #('1', 'housing', 'gs://test-deployments/test-deployment-1/simple-test-model/', 'gs://test-deployments/test-deployment-1/housing.csv')"""
    record = (modelName, modelPublicIP, modelLocation, dataLocation)
    try:
        # Execute the SQL command
        cursor.execute(sql,record)
        # Commit your changes in the database
        db.commit()
        print(cursor.rowcount, "models inserted successfully into Deployment service")
    except:
        # Rollback in case there is any error
        db.rollback()
        print("Data not inserted properly")
    # disconnect from server
    db.close()

def get_db_conn():
    db = pymysql.connect(
        host = '34.72.46.205',
        user = 'root',
        password = 'CUBoulder@2022',
        database = 'ml_deployment',
        charset = 'utf8mb4',
        cursorclass = pymysql.cursors.DictCursor
    )

    return db

def get_model_name_from_bucket_name(storage_bucket: str) -> str:
    """
    Returns the name of the folder that contains the SavedModel given
    the full path of the bucket in which it is stored.
    eg. "gs://test-deployments/test-deployment-1/simple-test-model/" -> "simple-test-model"
    """
    split_string = storage_bucket.split('/')
    model_name = split_string[-2] if split_string[-1] == '' else split_string[-1]
    return model_name

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

def deploy_model(model_bucket: str, model_name: str, data_bucket: str):
    """
    Deploys a model onto the K8S cluster.
    """
    model_bucket_escaped = model_bucket.replace('/', '\/')
    data_bucket_escaped = data_bucket.replace('/', '\/')

    # Change grpc-cloudbuild.yaml and grpc-deployment.yaml to use specified model
    os.system(f"sed -i 's/model_name/{model_name}/g' grpc-deployment.yaml grpc-cloudbuild.yaml")
    os.system(f"sed -i 's/model_bucket/{model_bucket_escaped}/g' grpc-cloudbuild.yaml")
    os.system(f"sed -i 's/data_bucket/{data_bucket_escaped}/g' grpc-cloudbuild.yaml")

    # Run the gcloud command to build and push the model to artifact registry
    os.system("gcloud builds submit --region=us-central1 --config=grpc-cloudbuild.yaml")

    # Deploy the model on the K8S cluster
    os.system("kubectl apply -f grpc-deployment.yaml")

    # Change the config files back to their template form
    os.system(f"sed -i 's/{data_bucket_escaped}/data_bucket/g' grpc-cloudbuild.yaml")
    os.system(f"sed -i 's/{model_bucket_escaped}/model_bucket/g' grpc-cloudbuild.yaml")
    os.system(f"sed -i 's/{model_name}/model_name/g' grpc-deployment.yaml grpc-cloudbuild.yaml")
    

    pod_status, service_ip = wait_for_deployment(model_name)
    return pod_status, service_ip


@app.route('/deleteModel/<string:model_name>', methods=['POST'])
def delete_model(model_name):
    """
    Deletes a deployment and its associate service given the name of a 
    model. Also deletes the model's data table and relevant metadata.
    """
    # Delete the K8S deployment and service
    os.system(f"sed -i 's/model_name/{model_name}/g' grpc-deployment.yaml \
                && kubectl delete -f grpc-deployment.yaml \
                && sed -i 's/{model_name}/model_name/g' grpc-deployment.yaml")

    # Delete the table from SQL and the metadata row
    db = get_db_conn()
    cursor = db.cursor()
    sql_delete_metadata = f"DELETE FROM ml_deployment.model_info WHERE model_name = '{model_name}';"
    sql_delete_table = f"DROP TABLE IF EXISTS ml_deployment.`{model_name}`;"

    try:
        # Execute the SQL command then close the DB connection
        cursor.execute(sql_delete_metadata)
        cursor.execute(sql_delete_table)
        db.commit()
        db.close()

        response = Response(status=200, mimetype="application/json")
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    except Exception as e:
        print(e)
        db.close()
        response = Response(status=500, mimetype="application/json")
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response


@app.route('/deployModel', methods=['POST'])
def deployModel():
    data = jsonpickle.decode(request.data)
    model_location, data_location = data['model_location'], data['data_location']

    # req_body = request.get_json()
    # split data to post to mysql
    model_name = get_model_name_from_bucket_name(model_location)
    
    # Deploy model to K8S
    pod_status, service_ip = deploy_model(model_location, model_name, data_location)
    response = jsonpickle.encode({'pod_status': pod_status, 'public_ip': service_ip})

    # Delete deployment if it failed
    # if pod_status != 'Running':
    #     print("Deployment failed, deleting deployment.")
    #     delete_model(model_name)
    # else:
    #     # Insert metadata into SQL
    insertModelInfoToSQL(model_name, service_ip, model_location, data_location)
    

    # Return response
    return Response(response=response, status=200, mimetype="application/json")
    

@app.route('/listModels', methods=['GET'])
def listModels():
    """
    Returns a list of all currently deployed modeld from table
    'model_info'
    """
    # Open database connection and prepare cursor object 
    db = get_db_conn()
    cursor = db.cursor()
    sql = "SELECT * FROM ml_deployment.model_info"

    try:
        # Execute the SQL command then close the DB connection
        cursor.execute(sql)
        db_response = cursor.fetchall()
        db.close()

        # Parse the DB response for only the info needed
        response_data = {'models': [model_object['model_name'] for model_object in db_response]}

        response_data = jsonpickle.encode(response_data)
        response =  Response(response=response_data, status=200, mimetype="application/json")
        response.headers['Access-Control-Allow-Origin'] = '*'

        return response

    except Exception as e:
        print(e)
        db.close()

        response_data = jsonpickle.encode({"Error": "Unable to fetch data."})
        response = Response(response=response_data, status=500, mimetype="application/json")
        response.headers['Access-Control-Allow-Origin'] = '*'

        return response


def compute_col_stats(train_vect, prod_vect, n) -> dict:
    """
    Helper function to compute the coulumn-wise statistics
    for the dashboard.
    """
    # Object to be returned
    stats = {'prod': {}, 'train': {}, 'bin_edges': None}
    
    # Max and min for each slice
    stats['train']['max'] = float(np.max(train_vect))
    stats['train']['min'] = float(np.min(train_vect))

    stats['prod']['max'] = float(np.max(prod_vect))
    stats['prod']['min'] = float(np.min(prod_vect))

    # Info for generating histogram
    n_bins = int(np.sqrt(n))
    abs_max = max(stats['train']['max'], stats['prod']['max'])
    abs_min = min(stats['train']['min'], stats['prod']['min'])

    # Histogram info
    train_heights, bin_edges = np.histogram(train_vect, bins=n_bins, range=(abs_min,abs_max))
    prod_heights, _ = np.histogram(prod_vect, bins=n_bins, range=(abs_min,abs_max))
    stats['train']['chart_bin_heights'] = list(train_heights.tolist())
    stats['prod']['chart_bin_heights'] = list(prod_heights.tolist())
    stats['bin_edges'] = list(bin_edges.tolist())

    # Average, stddev, and median for each slice
    stats['train']['average'] = float(np.average(train_vect))
    stats['train']['stddev'] = float(np.std(train_vect))
    stats['train']['median'] = float(np.median(train_vect))

    stats['prod']['average'] = float(np.average(prod_vect))
    stats['prod']['stddev'] = float(np.std(prod_vect))
    stats['prod']['median'] = float(np.median(prod_vect))

    return stats

@app.route('/dashboard/<string:model_name>', methods=['GET', 'POST'])
def get_dashboard_info(model_name):
    """
    Returns data that gets displayed in a model's dashboard. Currently
    queries whole table then does processing in Python. 
    """
    db = get_db_conn()
    cursor = db.cursor()

    # Get the whole table to do processing
    whole_table_query = f"SELECT * FROM ml_deployment.`{model_name}`"
    cursor.execute(whole_table_query)
    data = cursor.fetchall()
    n = len(data)
    
    # Get names of feature and result columns
    col_names = list(data[0].keys())
    col_names = [col for col in col_names if col not in ['dataset', 'id', 'date']]
    
    # Compute column-level stats for train and prod, respectively
    response = {'data': {}}
    for feature in col_names:
        # Form the arrays on which to compute statistics
        train_vect = np.array([row[feature] for row in data if row['dataset'] == 'train'])
        prod_vect = np.array([row[feature] for row in data if row['dataset'] == 'prod'])

        # Save the result in the response
        response['data'][feature] = compute_col_stats(train_vect, prod_vect, n)


    response['num_preds'] = len(prod_vect)

    # Get other metadata needed for the dashboard page
    metadata_sql = \
        f"""
        SELECT * FROM ml_deployment.model_info
        WHERE model_name='{model_name}'
         """
    cursor.execute(metadata_sql)
    metadata = cursor.fetchall()[0]
    db.close()

    response['model_name'] = model_name
    response['public_ip'] = metadata['model_public_ip']

    # Encode and return the response
    response_pickled = jsonpickle.encode(response)
    response = Response(response=response_pickled, status=200, mimetype="application/json")
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

# createTable()
app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)