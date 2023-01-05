import requests
import json
import jsonpickle
import sys
import pprint

if __name__ == "__main__":
    route = sys.argv[1]
    pp = pprint.PrettyPrinter(indent=1)

    base_url = "http://35.193.203.116:5000"
    headers = {'content-type': 'application/json'}

    if route == 'deploy':
        url = base_url + "/deployModel"
        payload = {
            'model_location': 'gs://test-deployments/test-deployment-1/new-test-model/',
            'data_location': 'gs://test-deployments/test-deployment-1/train.json'
        }
    elif route == 'delete':
        url = base_url + "/deleteModel/new-test-model"
        payload = {
            'model_name': 'new-test-model'
        }

    elif route == 'dashboard':
        url = base_url + '/dashboard/new-test-model'
        payload = None

    elif route == 'models':
        url = base_url + '/listModels'
        payload = None
        payload_pickled = jsonpickle.encode(payload)
        response = requests.get(url, headers=headers, data=payload_pickled)

        print("Response is", response)
        print(json.loads(response.text))
        exit()

    else:
        print("Error: Invalid route supplied. Exiting program.")
        exit()

    
    payload_pickled = jsonpickle.encode(payload)
    response = requests.post(url, headers=headers, data=payload_pickled)

    print("Response is", response)
    if route in ['deploy', 'dashboard']:
        # pp.pprint(json.loads(response.text))
        response_json = response.json()
        pp.pprint(response_json)
        # ex = response_json['data']['zn']['prod']['average']
        # print(ex)