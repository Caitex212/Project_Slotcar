import json

def load_data(filename, type):
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        if type == 1:
            data = []
        else:
            data = {}
    except json.JSONDecodeError:
        if type == 1:
            data = []
        else:
            data = {}
    return data

def save_data(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file)