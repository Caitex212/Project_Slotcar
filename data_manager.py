import json

def load_data(filename):
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}
    except json.JSONDecodeError:
        data = {}
    return data

def save_data(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file)