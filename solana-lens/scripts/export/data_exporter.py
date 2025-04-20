import json
import csv
import pandas as pd
import os
from typing import Dict, List, Any, Optional, Union
import logging
from datetime import datetime

class DataExporter:
    """
    Utility for exporting analysis data to various formats for visualization and reporting.
    
    This class handles exporting data to CSV, JSON, and other formats for use in
    visualization tools and research reports.
    """
    
    def __init__(self, output_dir: str = 'data'):
        """
        Initialize the data exporter with an output directory.
        
        Args:
            output_dir (str): Base directory for data output
        """
        self.output_dir = output_dir
        # Create shared data directory structure if needed
        self.viz_data_dir = os.path.join(output_dir, 'viz')
        os.makedirs(self.viz_data_dir, exist_ok=True)
    
    def export_for_visualization(self, data: Any, dataset_name: str, dataset_type: str = None):
        """
        Export data specifically formatted for visualizations.
        
        Args:
            data: The data to export (dict, list, etc.)
            dataset_name (str): Name of the dataset
            dataset_type (str, optional): Type of the dataset (e.g., 'network', 'timeline')
        
        Returns:
            str: Path to the exported file
        """
        # Create a subfolder for the specific visualization type if provided
        target_dir = self.viz_data_dir
        if dataset_type:
            target_dir = os.path.join(self.viz_data_dir, dataset_type)
            os.makedirs(target_dir, exist_ok=True)
        
        # Add timestamp to filename to avoid overwrites
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{dataset_name}_{timestamp}.json"
        filepath = os.path.join(target_dir, filename)
        
        # Create a metadata wrapper for the data
        metadata = {
            "dataset_name": dataset_name,
            "dataset_type": dataset_type,
            "generated_at": datetime.now().isoformat(),
            "data": data
        }
        
        # Write to JSON file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            # Also create a "latest" version for easy access
            latest_filepath = os.path.join(target_dir, f"{dataset_name}_latest.json")
            with open(latest_filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)
                
            logging.info(f"Data exported for visualization to {filepath}")
            return filepath
        except Exception as e:
            logging.error(f"Failed to export data for visualization: {e}")
            return None
    
    def export_json(self, data: Any, filename: str, subdirectory: str = None) -> str:
        """
        Export data to a JSON file.
        
        Args:
            data: The data to export
            filename (str): Output filename
            subdirectory (str, optional): Subdirectory within output_dir
            
        Returns:
            str: Path to the exported file
        """
        directory = self.output_dir
        if subdirectory:
            directory = os.path.join(directory, subdirectory)
            os.makedirs(directory, exist_ok=True)
            
        filepath = os.path.join(directory, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            logging.info(f"Data exported to {filepath}")
            return filepath
        except Exception as e:
            logging.error(f"Failed to export JSON: {e}")
            return None
    
    def export_csv(self, data: List[Dict], filename: str, subdirectory: str = None) -> str:
        """
        Export data to a CSV file.
        
        Args:
            data (List[Dict]): List of dictionaries to export
            filename (str): Output filename
            subdirectory (str, optional): Subdirectory within output_dir
            
        Returns:
            str: Path to the exported file
        """
        if not data:
            logging.warning("No data to export to CSV")
            return None
            
        directory = self.output_dir
        if subdirectory:
            directory = os.path.join(directory, subdirectory)
            os.makedirs(directory, exist_ok=True)
            
        filepath = os.path.join(directory, filename)
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            logging.info(f"Data exported to {filepath}")
            return filepath
        except Exception as e:
            logging.error(f"Failed to export CSV: {e}")
            return None
    
    def export_graph_data(self, 
                         nodes: List[Dict], 
                         links: List[Dict], 
                         name: str, 
                         metadata: Dict = None) -> str:
        """
        Export network graph data in the format expected by D3 visualizations.
        
        Args:
            nodes (List[Dict]): List of node objects
            links (List[Dict]): List of link objects
            name (str): Name of the graph
            metadata (Dict, optional): Additional metadata
            
        Returns:
            str: Path to the exported file
        """
        graph_data = {
            "nodes": nodes,
            "links": links,
            "metadata": metadata or {
                "name": name,
                "generated_at": datetime.now().isoformat()
            }
        }
        
        # Ensure the network directory exists
        network_dir = os.path.join(self.viz_data_dir, 'network')
        os.makedirs(network_dir, exist_ok=True)
        
        # Create timestamp and filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{name}_network_{timestamp}.json"
        filepath = os.path.join(network_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(graph_data, f, indent=2, default=str)
            
            # Also create a "latest" version
            latest_filepath = os.path.join(network_dir, f"{name}_network_latest.json")
            with open(latest_filepath, 'w', encoding='utf-8') as f:
                json.dump(graph_data, f, indent=2, default=str)
                
            logging.info(f"Network graph data exported to {filepath}")
            return filepath
        except Exception as e:
            logging.error(f"Failed to export network graph data: {e}")
            return None

    @staticmethod
    def export_to_csv(data: Union[List[Dict], pd.DataFrame], filename: str, index: bool = False) -> None:
        """
        Export data to CSV file.
        
        Args:
            data (Union[List[Dict], pd.DataFrame]): Data to export
            filename (str): Output filename
            index (bool, optional): Whether to include index. Defaults to False.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Convert list of dicts to DataFrame if necessary
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data
        
        # Export to CSV
        df.to_csv(filename, index=index)
        print(f"Data exported to CSV: {filename}")

    @staticmethod
    def export_to_json(data: Any, filename: str, pretty: bool = True) -> None:
        """
        Export data to JSON file.
        
        Args:
            data (Any): Data to export
            filename (str): Output filename
            pretty (bool, optional): Whether to format JSON with indentation. Defaults to True.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Export to JSON
        with open(filename, 'w') as f:
            if pretty:
                json.dump(data, f, indent=2)
            else:
                json.dump(data, f)
        
        print(f"Data exported to JSON: {filename}")

    @staticmethod
    def export_to_excel(data: Union[Dict[str, pd.DataFrame], pd.DataFrame], filename: str) -> None:
        """
        Export data to Excel file.
        
        Args:
            data (Union[Dict[str, pd.DataFrame], pd.DataFrame]): Data to export
            filename (str): Output filename
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Check if data is a dict of DataFrames (for multiple sheets)
        if isinstance(data, dict):
            with pd.ExcelWriter(filename) as writer:
                for sheet_name, df in data.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            # Single DataFrame
            data.to_excel(filename, index=False)
        
        print(f"Data exported to Excel: {filename}")

    @staticmethod
    def export_to_d3_json(nodes: List[Dict], links: List[Dict], filename: str) -> None:
        """
        Export network data to D3.js compatible JSON format.
        
        Args:
            nodes (List[Dict]): Node data
            links (List[Dict]): Link/edge data
            filename (str): Output filename
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Create D3 format data
        d3_data = {
            "nodes": nodes,
            "links": links
        }
        
        # Export to JSON
        with open(filename, 'w') as f:
            json.dump(d3_data, f, indent=2)
        
        print(f"Network data exported for D3.js: {filename}")

    @staticmethod
    def export_to_observable(data: Dict, filename: str) -> None:
        """
        Export data for Observable notebook.
        
        Args:
            data (Dict): Data to export
            filename (str): Output filename
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Format for Observable
        observable_data = {
            "data": data,
            "metadata": {
                "exported_at": pd.Timestamp.now().isoformat(),
                "format_version": "1.0"
            }
        }
        
        # Export to JSON
        with open(filename, 'w') as f:
            json.dump(observable_data, f, indent=2)
        
        print(f"Data exported for Observable: {filename}")

    @staticmethod
    def export_timeseries_for_chart(data: List[Dict], x_field: str, y_fields: List[str], 
                                   filename: str, format: str = "json") -> None:
        """
        Export time series data formatted for charting libraries.
        
        Args:
            data (List[Dict]): Time series data
            x_field (str): Field name for x-axis (typically a timestamp)
            y_fields (List[str]): Field names for y-axis values
            filename (str): Output filename
            format (str, optional): Output format ('json' or 'csv'). Defaults to "json".
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Format data for charting
        chart_data = []
        
        for item in data:
            entry = {x_field: item.get(x_field)}
            
            for field in y_fields:
                entry[field] = item.get(field)
            
            chart_data.append(entry)
        
        # Export based on format
        if format.lower() == "csv":
            with open(filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[x_field] + y_fields)
                writer.writeheader()
                writer.writerows(chart_data)
        else:
            with open(filename, 'w') as f:
                json.dump(chart_data, f, indent=2)
        
        print(f"Time series data exported for charting: {filename}")

    @staticmethod
    def export_for_dune(data: pd.DataFrame, filename: str) -> None:
        """
        Export data in a format suitable for Dune Analytics.
        
        Args:
            data (pd.DataFrame): Data to export
            filename (str): Output filename
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Dune typically works with CSV files
        data.to_csv(filename, index=False)
        
        # Also create SQL-friendly column names
        sql_friendly_df = data.copy()
        sql_friendly_df.columns = [col.lower().replace(' ', '_') for col in sql_friendly_df.columns]
        
        sql_filename = filename.replace('.csv', '_sql_friendly.csv')
        sql_friendly_df.to_csv(sql_filename, index=False)
        
        print(f"Data exported for Dune Analytics: {filename} and {sql_filename}")

    @staticmethod
    def export_markdown_report(title: str, sections: List[Dict], filename: str) -> None:
        """
        Export analysis results as a Markdown report.
        
        Args:
            title (str): Report title
            sections (List[Dict]): Report sections with 'title' and 'content' keys
            filename (str): Output filename
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Create markdown content
        markdown = f"# {title}\n\n"
        markdown += f"*Generated on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        
        for section in sections:
            markdown += f"## {section['title']}\n\n"
            markdown += f"{section['content']}\n\n"
        
        # Write to file
        with open(filename, 'w') as f:
            f.write(markdown)
        
        print(f"Markdown report exported: {filename}")

    @staticmethod
    def export_interactive_html_table(data: pd.DataFrame, filename: str, title: str = "") -> None:
        """
        Export DataFrame as an interactive HTML table using DataTables.
        
        Args:
            data (pd.DataFrame): Data to export
            filename (str): Output filename
            title (str, optional): Table title. Defaults to "".
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Create HTML with DataTables
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css">
            <script type="text/javascript" src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
            <script type="text/javascript" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 8px; text-align: left; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{title}</h1>
                <p>Generated on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <table id="dataTable" class="display">
                    <thead>
                        <tr>
                            {" ".join([f"<th>{col}</th>" for col in data.columns])}
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(["<tr>" + " ".join([f"<td>{str(value)}</td>" for value in row]) + "</tr>" for _, row in data.iterrows()])}
                    </tbody>
                </table>
            </div>
            
            <script>
                $(document).ready(function() {{
                    $('#dataTable').DataTable({{
                        pageLength: 25,
                        order: [[0, 'asc']]
                    }});
                }});
            </script>
        </body>
        </html>
        """
        
        # Write to file
        with open(filename, 'w') as f:
            f.write(html)
        
        print(f"Interactive HTML table exported: {filename}")

    @staticmethod
    def export_html_report(title: str, sections: List[Dict], filename: str) -> None:
        """
        Export analysis results as an HTML report.
        
        Args:
            title (str): Report title
            sections (List[Dict]): Report sections with 'title', 'content' and optional 'chart' keys
            filename (str): Output filename
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Create HTML content
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                h1, h2 {{ color: #333; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .section {{ margin-bottom: 30px; }}
                .chart {{ margin: 20px 0; }}
                pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{title}</h1>
                <p>Generated on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        for section in sections:
            html += f"""
                <div class="section">
                    <h2>{section['title']}</h2>
                    <div class="content">
                        {section['content']}
                    </div>
            """
            
            if 'chart' in section:
                html += f"""
                    <div class="chart">
                        {section['chart']}
                    </div>
                """
            
            html += "</div>"
        
        html += """
            </div>
        </body>
        </html>
        """
        
        # Write to file
        with open(filename, 'w') as f:
            f.write(html)
        
        print(f"HTML report exported: {filename}")