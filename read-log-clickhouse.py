from joblib import Parallel, delayed
from os import listdir
from io import StringIO
import pandas as pd
import numpy as np
import clickhouse_connect
import gc
import csv


def insert_logs(directory, filename):
    client = clickhouse_connect.get_client(host="localhost")

    print(f"exporting {filename}")
    raw = pd.read_csv(f"{directory}/{filename}", sep="\t", names=["data"])
    raw["data"] = raw["data"].str.replace("\\'", "")
    raw["data"] = raw["data"].str.replace("\\\\", "")
    raw["data"] = raw["data"].replace(" [Your log message was truncated]", np.nan)
    raw["data"] = raw["data"].str.replace("`", "")
    raw.dropna(subset=["data"], inplace=True)
    raw_string = raw.to_csv(
        index=False, header=False, sep="\n", quoting=csv.QUOTE_NONE, lineterminator="\n"
    )

    df = pd.read_csv(
        StringIO(raw_string),
        names=[
            "timestamp",
            "serverhost",
            "username",
            "host",
            "connectionid",
            "queryid",
            "operation",
            "database",
            "object",
            "retcode",
        ],
        skip_blank_lines=True,
        dtype={"connectionid": "Int64", "queryid": "Int64", "retcode": "Int8"},
        sep=",",
        quotechar="'",
        on_bad_lines="warn",
        doublequote=False,
        engine="python",
        encoding="utf-8",
    )

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, unit="us")
    df["connectionid"] = df["connectionid"].fillna(0)
    df["queryid"] = df["queryid"].fillna(0)
    df["retcode"] = df["retcode"].fillna(-1)
    df["host"] = df["host"].astype("S")
    df["operation"] = df["operation"].astype("S")
    df["database"] = df["database"].astype("S")
    df["username"] = df["username"].astype("S")
    df["serverhost"] = df["serverhost"].astype("S")
    df["object"] = df["object"].astype("unicode")

    client.insert_df(table="rds_audit_logs", database="logs", df=df)
    gc.collect()


if __name__ == "__main__":
    path = "./.raw_data/ffi-krdv-l2alpha-amy-prd-node-mstr/"
    file_list = listdir(path)
    # file_list = ["audit.log.0.2024-03-18-14-40.1"]

    Parallel(n_jobs=4, prefer="threads")(
        delayed(insert_logs)(directory=path, filename=file) for file in file_list
    )
