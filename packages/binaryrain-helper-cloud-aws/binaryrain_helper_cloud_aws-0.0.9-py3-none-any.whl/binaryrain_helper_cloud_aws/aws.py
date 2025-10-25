import boto3
from aws_lambda_powertools.utilities import parameters


def get_secret_data(secret_name: str) -> dict:
    """
    Get secret data from AWS Secrets Manager.

    :param str secret_name:
        Name of the secret to retrieve.

    :returns dict:
        Secret data as a dictionary.
    """
    if not secret_name:
        raise ValueError("No secret name provided.")

    secret_data = parameters.get_secret(secret_name, transform="json")

    return secret_data


def get_app_config(
    AppConfig_environment: str, AppConfig_application: str, AppConfig_profile: str
) -> dict:
    """
    Load configuration from AWS AppConfig.

    :param str AppConfig_environment:
        Name of the AppConfig environment.
    :param str AppConfig_application:
        Name of the AppConfig application.
    :param str AppConfig_profile:
        Name of the AppConfig profile.

    :returns dict:
        Configuration data as a dictionary.
    """

    # validate input parameters
    if not AppConfig_environment:
        raise ValueError("No environment provided.")
    if not AppConfig_application:
        raise ValueError("No application provided.")
    if not AppConfig_profile:
        raise ValueError("No profile provided.")

    app_config = parameters.get_app_config(
        name=AppConfig_profile,
        environment=AppConfig_environment,
        application=AppConfig_application,
        transform="json",
    )

    return app_config


def load_file_from_s3(filename: str, s3_bucket: str) -> bytes:
    """
    Load file from S3 bucket.

    :param str filename:
        Name of the file in S3 to load.
    :param str s3_bucket:
        Name of the S3 bucket where the file is stored.

    :returns bytes:
        File contents as bytes.
    """

    # validate input parameters
    if not filename:
        raise ValueError("No filename provided.")
    if not s3_bucket:
        raise ValueError("No S3 bucket provided.")

    s3_client = boto3.client("s3")
    file_obj = s3_client.get_object(Bucket=s3_bucket, Key=filename)

    return file_obj["Body"].read()


def save_file_to_s3(
    filename: str,
    s3_bucket: str,
    file_contents: bytes,
    server_side_encryption: str = None,
    sse_kms_key_id: str = None,
) -> bool:
    """
    Save file to S3 bucket.

    :param str filename:
        Name of the file to save in S3.
    :param str s3_bucket:
        Name of the S3 bucket where the file will be saved.
    :param bytes file_contents:
        Contents of the file to save.
    :param str server_side_encryption: (optional)
        Type of server side encryption.
    :param str sse_kms_key_id: (optional)
        KMS key ID for server side encryption.

    :returns bool:
        Indicates whether the file got saved successfully, otherwise false.
    """

    # validate input parameters
    if not filename:
        raise ValueError("No filename provided.")
    if not s3_bucket:
        raise ValueError("No S3 bucket provided.")
    if not file_contents or not isinstance(file_contents, bytes) or len(file_contents) == 0:
        raise ValueError(
            "No file contents provided or file contents are empty or not of type bytes."
        )

    # if server side encryption is provided, make sure the KMS key ID is also provided
    if server_side_encryption and not sse_kms_key_id:
        raise ValueError("SSE requested, but no KMS key ID provided for server side encryption.")

    s3_client = boto3.client("s3")

    # if server side encryption is provided, use it
    if server_side_encryption:
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=filename,
            Body=file_contents,
            ServerSideEncryption=server_side_encryption,
            SSEKMSKeyId=sse_kms_key_id,
        )
    else:
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=filename,
            Body=file_contents,
        )


def get_s3_presigned_url_readonly(filename: str, s3_bucket: str, expires_in: int = 120) -> str:
    """
    Get a presigned URL for a file in S3.

    :param str filename:
        Name of the file in S3.
    :param str s3_bucket:
        Name of the S3 bucket where the file is stored.
    :param int expires_in: (optional)
        Expiration time for the presigned URL in seconds. Default is 120 seconds.

    :returns str:
        Presigned URL for the file in S3.
    """

    # validate input parameters
    if not filename:
        raise ValueError("No filename provided.")
    if not s3_bucket:
        raise ValueError("No S3 bucket provided.")

    # create S3 client
    s3_client = boto3.client("s3")
    presigned_url = s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": s3_bucket, "Key": filename},
        ExpiresIn=expires_in,
    )

    # return the presigned URL
    return presigned_url


def move_file_in_s3(
    source_bucket: str, source_filename: str, destination_filename: str, destination_bucket: str
) -> bool:
    """
    Move a file within S3 by copying and deleting the original.

    :param str source_bucket:
        Name of the S3 bucket where the source file is stored.
    :param str source_filename:
        Name of the source file in S3.
    :param str destination_filename:
        Name of the destination file in S3.
    :param str destination_bucket:
        Name of the S3 bucket where the destination file will be stored.

    :returns bool:
        Indicates whether the file got moved successfully, otherwise false.
    """

    # validate input parameters
    if not source_bucket:
        raise ValueError("No source bucket provided.")
    if not source_filename:
        raise ValueError("No source filename provided.")
    if not destination_filename:
        raise ValueError("No destination filename provided.")
    if not destination_bucket:
        raise ValueError("No destination bucket provided.")

    s3_client = boto3.client("s3")

    # copy the object to the new location
    s3_client.copy_object(
        CopySource={"Bucket": source_bucket, "Key": source_filename},
        Bucket=destination_bucket,
        Key=destination_filename,
    )

    # delete the original object
    s3_client.delete_object(Bucket=source_bucket, Key=source_filename)

    # return true if the operation was successful
    # exception handling will be done by the caller
    # in order to provide more context on the error
    return True
