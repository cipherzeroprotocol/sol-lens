import csv

def export_to_csv(data, filepath):
    """
    Exports data to a CSV file.

    Args:
        data (list of dict): The data to be exported. Each dictionary represents a row.
        filepath (str): The path to the CSV file.
    """
    try:
        with open(filepath, 'w', newline='') as f:
            if data:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            print(f"Data successfully exported to {filepath}")
    except Exception as e:
        print(f"Error exporting to CSV: {e}")

if __name__ == '__main__':
    # Example usage
    example_data = [
        {"name": "Alice", "age": 30, "city": "New York"},
        {"name": "Bob", "age": 25, "city": "Los Angeles"},
        {"name": "Charlie", "age": 35, "city": "Chicago"}
    ]
    export_to_csv(example_data, "example.csv")
