@testing_solution
@s3
@boto3
Feature: Test Boto3 S3 client module

    @go_nogo
    Scenario: Simple file put and get

        ### PRECONDITIONS - BEGIN
        Given begin preconditions
        
        Given SERVER = start internal S3 server

        Given CLIENT = new internal Boto3 S3 client
        
        Given end preconditions
        ### PRECONDITIONS - END
        
        # Verify buckets are empty
        When RESULT = list of buckets (S3 client: CLIENT)
        Then RESULT is empty list
        
        # Create bucket and verify it is empty
        When create bucket 'my-bucket' (S3 client: CLIENT)

        When RESULT = list of buckets (S3 client: CLIENT)
        Then RESULT is list
            | 'my-bucket' |
        
        When RESULT = list of objects in bucket 'my-bucket' (S3 client: CLIENT)
        When RESULT = convert list RESULT to table with object attributes as columns
        Then table RESULT is empty
        
        # Add a file with 2 keys
        Given FILE = create CSV file with prefix 'file'
            | Column 1  | Column 2  |
            | 'Value 1' | 'Value 2' |
        Given FILE_CONTENT = content of file FILE
        
        When put file FILE in object 'file1' in bucket 'my-bucket' (S3 client: CLIENT)
        When put file FILE in object '/tmp/file1' in bucket 'my-bucket' (S3 client: CLIENT)
        
        # Verify bucket objects
        When RESULT = list of objects in bucket 'my-bucket' (S3 client: CLIENT)
        When RESULT = convert list RESULT to table with object attributes as columns
        Then table RESULT is
            | Key           | LastModified  | ETag  | ChecksumAlgorithm | Size  | StorageClass  |
            | '/tmp/file1'  | N/A           | N/A   | N/A               | 36    | N/A           |
            | 'file1'       | N/A           | N/A   | N/A               | 36    | N/A           |
        
        # Verify bucket objects with filters
        When RESULT = list of objects in bucket 'my-bucket' (S3 client: CLIENT)
            | Prefix |
            | 'file' |
        When RESULT = convert list RESULT to table with object attributes as columns
        Then table RESULT is
            | Key           | LastModified  | ETag  | ChecksumAlgorithm | Size  | StorageClass  |
            | 'file1'       | N/A           | N/A   | N/A               | 36    | N/A           |
        
        # WARNING: verification of file content is commented due to a problem of access denied in Moto server
        Given next step shall fail on exception matching 'An error occurred \(403\) when calling the GetObject operation: Forbidden'
        When RESULT_GET = data of object 'file1' in bucket 'my-bucket' (S3 client: CLIENT)
        #Then RESULT_GET == FILE_CONTENT
        
        Given DEST_PATH = scenario report directory 's3_client'
        Given OBTAINED_FILE = '${DEST_PATH}/obtained_file1.csv'

        # WARNING: verification of file content is commented due to an incompatibility between Minio client and Moto server
        Given next step shall fail on exception matching 'An error occurred \(403\) when calling the HeadObject operation: Forbidden'
        When get file OBTAINED_FILE from object 'file1' in bucket 'my-bucket' (S3 client: CLIENT)
        #Given OBTAINED_FILE_CONTENT = content of file OBTAINED_FILE
        #Then OBTAINED_FILE_CONTENT == FILE_CONTENT
        
