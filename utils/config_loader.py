import json

def load_config(filename='config.json'):
    try:
        with open(filename, 'r') as config_file:
            config = json.load(config_file)
            return config
    except FileNotFoundError:
        print(f"File {filename} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Failed to parse {filename}.")
        return None
