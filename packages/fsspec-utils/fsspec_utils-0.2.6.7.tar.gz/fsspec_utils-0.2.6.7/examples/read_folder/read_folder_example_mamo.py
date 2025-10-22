"""Learn more about Marimo: https://marimo.io"""

import marimo

__generated_with = "0.2.2"
app = marimo.App()


@app.cell
def __():
    import tempfile
    import shutil
    import os
    import polars as pl
    import pyarrow as pa
    import pyarrow.parquet as pq
    import json

    # Import fsspec-utils
    from fsspec_utils import filesystem
    return filesystem, json, os, pa, pl, pq, shutil, tempfile


@app.cell
def __(os, pl):
    def create_sample_data(temp_dir):
        """Create sample Parquet, CSV, and JSON files in subdirectories."""
        
        # Create subdirectories
        subdir1 = os.path.join(temp_dir, "subdir1")
        subdir2 = os.path.join(temp_dir, "subdir2")
        os.makedirs(subdir1, exist_ok=True)
        os.makedirs(subdir2, exist_ok=True)
        
        # Sample data
        data1 = {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "value": [10.5, 20.3, 30.7]
        }
        
        data2 = {
            "id": [4, 5, 6],
            "name": ["David", "Eve", "Frank"],
            "value": [40.2, 50.8, 60.1]
        }
        
        # Create Parquet files
        df1 = pl.DataFrame(data1)
        df2 = pl.DataFrame(data2)
        
        # Save Parquet files
        df1.write_parquet(os.path.join(subdir1, "data1.parquet"))
        df2.write_parquet(os.path.join(subdir2, "data2.parquet"))
        
        # Create CSV files
        df1.write_csv(os.path.join(subdir1, "data1.csv"))
        df2.write_csv(os.path.join(subdir2, "data2.csv"))
        
        # Create JSON files
        with open(os.path.join(subdir1, "data1.json"), "w") as f:
            json.dump(data1, f)
        
        with open(os.path.join(subdir2, "data2.json"), "w") as f:
            json.dump(data2, f)
        
        print(f"Created sample data in {temp_dir}")
        print(f"  - {subdir1}/data1.parquet")
        print(f"  - {subdir2}/data2.parquet")
        print(f"  - {subdir1}/data1.csv")
        print(f"  - {subdir2}/data2.csv")
        print(f"  - {subdir1}/data1.json")
        print(f"  - {subdir2}/data2.json")
    return create_sample_data,


@app.cell
def __(filesystem):
    def demonstrate_parquet_reading(temp_dir):
        """Demonstrate reading Parquet files into a PyArrow Table."""
        print("\n=== Reading Parquet Files ===")
        
        # Create a filesystem instance
        fs = filesystem(temp_dir)
        
        # Read all Parquet files in the directory and subdirectories
        # This returns a PyArrow Table directly
        parquet_table = fs.read_parquet("**/*.parquet", concat=True)
        
        print(f"Successfully read Parquet files into PyArrow Table")
        print(f"Table schema: {parquet_table.schema}")
        print(f"Table shape: {parquet_table.num_rows} rows x {parquet_table.num_columns} columns")
        print("First 3 rows:")
        print(parquet_table.slice(0, 3).to_pandas())
        
        return parquet_table
    return demonstrate_parquet_reading,


@app.cell
def __(filesystem):
    def demonstrate_csv_reading(temp_dir):
        """Demonstrate reading CSV files into a PyArrow Table."""
        print("\n=== Reading CSV Files ===")
        
        # Create a filesystem instance
        fs = filesystem(temp_dir)
        
        # Read all CSV files in the directory and subdirectories
        # This returns a Polars DataFrame when concat=True
        csv_df = fs.read_csv("**/*.csv", concat=True)
        
        print(f"Successfully read CSV files into Polars DataFrame")
        print(f"DataFrame shape: {csv_df.shape}")
        print("First 3 rows:")
        print(csv_df.head(3))
        
        # Convert Polars DataFrame to PyArrow Table
        csv_table = csv_df.to_arrow()
        
        print(f"\nConverted to PyArrow Table")
        print(f"Table schema: {csv_table.schema}")
        print(f"Table shape: {csv_table.num_rows} rows x {csv_table.num_columns} columns")
        
        return csv_table
    return demonstrate_csv_reading,


@app.cell
def __(filesystem):
    def demonstrate_json_reading(temp_dir):
        """Demonstrate reading JSON files into a PyArrow Table."""
        print("\n=== Reading JSON Files ===")
        
        # Create a filesystem instance
        fs = filesystem(temp_dir)
        
        # Read all JSON files in the directory and subdirectories
        # This returns a Polars DataFrame when as_dataframe=True and concat=True
        json_df = fs.read_json("**/*.json", as_dataframe=True, concat=True)
        
        print(f"Successfully read JSON files into Polars DataFrame")
        print(f"DataFrame shape: {json_df.shape}")
        print("First 3 rows:")
        print(json_df.head(3))
        
        # Convert Polars DataFrame to PyArrow Table
        json_table = json_df.to_arrow()
        
        print(f"\nConverted to PyArrow Table")
        print(f"Table schema: {json_table.schema}")
        print(f"Table shape: {json_table.num_rows} rows x {json_table.num_columns} columns")
        
        return json_table
    return demonstrate_json_reading,


@app.cell
def __(tempfile):
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    print(f"Created temporary directory: {temp_dir}")
    return temp_dir,


@app.cell
def __(create_sample_data, temp_dir):
    # Create sample data
    create_sample_data(temp_dir)
    return


@app.cell
def __(demonstrate_parquet_reading, temp_dir):
    # Demonstrate reading different file formats
    parquet_table = demonstrate_parquet_reading(temp_dir)
    return parquet_table,


@app.cell
def __(demonstrate_csv_reading, temp_dir):
    csv_table = demonstrate_csv_reading(temp_dir)
    return csv_table,


@app.cell
def __(demonstrate_json_reading, temp_dir):
    json_table = demonstrate_json_reading(temp_dir)
    return json_table,


@app.cell
def __(csv_table, json_table, parquet_table):
    # Verify that all tables have the same data
    print("\n=== Verification ===")
    print(f"All tables have the same number of rows: "
          f"{parquet_table.num_rows == csv_table.num_rows == json_table.num_rows}")
    print(f"All tables have the same number of columns: "
          f"{parquet_table.num_columns == csv_table.num_columns == json_table.num_columns}")
    return


@app.cell
def __(shutil, temp_dir):
    # Clean up temporary directory
    shutil.rmtree(temp_dir)
    print(f"\nCleaned up temporary directory: {temp_dir}")
    return


if __name__ == "__main__":
    app.run()