# Placeholder for future JSON exporter script
import json

def export_to_json(data, filepath):
    """
    Exports data to a JSON file.

    Args:
        data (dict or list): The data to be exported.
        filepath (str): The path to the JSON file.
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Data successfully exported to {filepath}")
    except Exception as e:
        print(f"Error exporting to JSON: {e}")

if __name__ == '__main__':
    # Example usage
    example_data = {
        "name": "Example",
        "value": 123
    }
    export_to_json(example_data, "example.json")
