import boto3
from joblib import Parallel, delayed
from os import path, makedirs
from botocore.exceptions import ClientError


def download_log(client, file, db_id):
    filename = path.join(".", ".raw_data", db_id, path.basename(file))
    makedirs(path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        print("downloading {rds} log file {file}".format(rds=db_id, file=file))
        token = "0"
        try:
            response = client.download_db_log_file_portion(
                DBInstanceIdentifier=db_id, LogFileName=file, Marker=token
            )
            while response["AdditionalDataPending"]:
                f.write(response["LogFileData"])
                token = response["Marker"]
                response = client.download_db_log_file_portion(
                    DBInstanceIdentifier=db_id, LogFileName=file, Marker=token
                )
            f.write(response["LogFileData"])
        except ClientError as e :
            print(e)


if __name__ == "__main__":
    client = boto3.client("rds", region_name="ap-southeast-3")

    cluster = client.describe_db_clusters(
        DBClusterIdentifier="ffi-krdv-l2alpha-amy-prd-cluster"
    )

    # db_instances = [ member.get("DBInstanceIdentifier", "") for member in cluster["DBClusters"][0].get("DBClusterMembers", []) ]
    db_instances = ["ffi-krdv-l2alpha-amy-prd-node-mstr"]

    for db in db_instances:
        db_log_files = client.describe_db_log_files(
            DBInstanceIdentifier=db,
            FilenameContains="audit",
        )
        files = [file.get("LogFileName") for file in db_log_files["DescribeDBLogFiles"]]
        files.sort()

        Parallel(n_jobs=8, prefer="threads")(
            delayed(download_log)(client=client, file=file, db_id=db) for file in files
        )
