"""Learn more about Marimo: https://marimo.io"""

import marimo

__generated_with = "0.2.2"
app = marimo.App()


@app.cell
def __():
    import pyarrow as pa
    import pyarrow.dataset as pds

    from fsspec_utils import filesystem
    from fsspec_utils.storage_options import AwsStorageOptions
    return AwsStorageOptions, filesystem, pa, pds


@app.cell
def __(AwsStorageOptions, filesystem):
    # Configure AWS S3 storage options
    # Replace with your actual AWS credentials and region
    s3_options = AwsStorageOptions(
        access_key_id="YOUR_AWS_ACCESS_KEY_ID",      # Replace with your AWS access key
        secret_access_key="YOUR_AWS_SECRET_ACCESS_KEY",  # Replace with your AWS secret key
        region="us-east-1",                      # AWS region
    )

    # Create fsspec filesystem instance from storage options
    fs = filesystem("s3", storage_options=s3_options)

    # Create PyArrow dataset from S3 bucket
    # Assumes Parquet data in s3://your-bucket/data/
    try:
        dataset = fs.pyarrow_dataset("s3://your-bucket/data/")
        
        # Read data from the dataset into a PyArrow table
        table = dataset.to_table()
        
        print(f"Dataset schema: {dataset.schema}")
        print(f"Table shape: {table.shape}")
        print(f"First few rows:\n{table.slice(0, 5)}")
    except Exception as e:
        print(f"Error reading from AWS S3: {e}")
        print("Make sure you have valid AWS credentials and the bucket exists.")
    return fs, s3_options


@app.cell
def __(AwsStorageOptions, filesystem):
    # Configure Cloudflare R2 storage options
    # R2 is S3-compatible, so we use AwsStorageOptions with a custom endpoint
    # Replace with your actual R2 credentials and account ID
    r2_options = AwsStorageOptions(
        access_key_id="YOUR_R2_ACCESS_KEY_ID",    # Replace with your R2 access key
        secret_access_key="YOUR_R2_SECRET_KEY",  # Replace with your R2 secret key
        endpoint_url="https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com",  # R2 endpoint URL
        # Note: R2 doesn't use AWS regions in the same way
    )

    # Create fsspec filesystem instance for R2
    r2_fs = filesystem("s3", storage_options=r2_options)

    # Create PyArrow dataset from R2 bucket
    try:
        r2_dataset = r2_fs.pyarrow_dataset("your-bucket-name/data/")
        
        # Read data from the R2 dataset
        r2_table = r2_dataset.to_table()
        
        print(f"R2 Dataset schema: {r2_dataset.schema}")
        print(f"R2 Table shape: {r2_table.shape}")
    except Exception as e:
        print(f"Error reading from Cloudflare R2: {e}")
        print("Make sure you have valid R2 credentials and the bucket exists.")
    return r2_fs, r2_options


@app.cell
def __(AwsStorageOptions, filesystem):
    # Configure MinIO storage options
    # MinIO is S3-compatible, so we use AwsStorageOptions with custom endpoint and credentials
    # Replace with your actual MinIO credentials and endpoint
    minio_options = AwsStorageOptions(
        access_key_id="YOUR_MINIO_ACCESS_KEY",               # Your MinIO access key
        secret_access_key="YOUR_MINIO_SECRET_KEY",           # Your MinIO secret key
        endpoint_url="http://localhost:9000",     # MinIO server endpoint
        allow_http=True,                          # Allow HTTP (not HTTPS) for local development
        # Note: MinIO doesn't require AWS regions
    )

    # Create fsspec filesystem instance for MinIO
    minio_fs = filesystem("s3", storage_options=minio_options)

    # Create PyArrow dataset from MinIO bucket
    try:
        minio_dataset = minio_fs.pyarrow_dataset("your-bucket/data/")
        
        # Read data from the MinIO dataset
        minio_table = minio_dataset.to_table()
        
        print(f"MinIO Dataset schema: {minio_dataset.schema}")
        print(f"MinIO Table shape: {minio_table.shape}")
    except Exception as e:
        print(f"Error reading from MinIO: {e}")
        print("Make sure you have a MinIO server running and the bucket exists.")
    return minio_fs, minio_options


@app.cell
def __(fs):
    # For partitioned Parquet data (e.g., data partitioned by date)
    try:
        partitioned_dataset = fs.pyarrow_dataset(
            "s3://your-bucket/partitioned-data/",
            partitioning=["year", "month", "day"]  # Hive-style partitioning
        )
        
        # Query with partition pruning - only read specific partitions
        filtered_table = partitioned_dataset.to_table(
            filter=(
                (partitioned_dataset.field("year") == 2024) &
                (partitioned_dataset.field("month") == 1) &
                (partitioned_dataset.field("day") > 15)
            )
        )
        
        print(f"Filtered table shape: {filtered_table.shape}")
    except Exception as e:
        print(f"Error working with partitioned dataset: {e}")
        print("Make sure you have a partitioned dataset in the specified location.")
    return


@app.cell
def __(fs):
    # If you have a _metadata file in your dataset directory
    try:
        parquet_dataset = fs.pyarrow_parquet_dataset("s3://your-bucket/data-with-metadata/")
        
        # This automatically uses the _metadata file for optimized reading
        optimized_table = parquet_dataset.to_table()
        
        print(f"Optimized table shape: {optimized_table.shape}")
        print(f"Dataset files: {parquet_dataset.files}")
    except Exception as e:
        print(f"Error reading optimized Parquet dataset: {e}")
        print("Make sure you have a dataset with a _metadata file in the specified location.")
    return


if __name__ == "__main__":
    app.run()