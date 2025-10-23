import requests
import json
import yaml

def callServer(method: str, url: str, host: str, headers: dict, params: dict):
    try:
        response = requests.request(method=method, url=url, headers=headers, params=params)
    except requests.ConnectionError as e:
        print("Error connecting to Joule server: {}".format(host))
        exit(1)
    return response


def postData(url: str, filename: str, params: dict, host: str, headers: dict):
    with open(filename) as json_data:

        ext = filename.split('.')[1].lower()
        if ext == "json":
            try:
                data = json.load(json_data)
            except json.decoder.JSONDecodeError as e:
                print("Error parsing JSON file")
                exit(1)
        elif ext == 'yaml' or ext == 'yml':
            try:
                data = yaml.load(json_data, Loader=yaml.FullLoader)
            except yaml.YAMLError as exc:
                print("Error parsing YAML file")
                exit(1)
        else:
            print("Invalid file type: {}".format(ext))
            exit(1)

        try:
            response = requests.post(url, headers=headers, json=data, params=params)
        except requests.ConnectionError as e:
            print("Error connecting to Joule server: {}".format(host))
            exit(1)
    return response