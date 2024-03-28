import csv
from joblib import Parallel, delayed
from fluent import sender
from os import listdir
import json


def send_logs(logger, directory, filename):
    print(f"exporting {filename}")
    with open(f"{directory}/{filename}", "r") as file:
        lines = file.readlines()

        for line in lines:
            if line == "":
                pass

            if line == " [Your log message was truncated]":
                pass

            row = list(csv.reader([line]))[0]

            if len(row) > 1:
                try:
                    log = {}

                    log["timestamp"] = int(row[0])
                    log["serverhost"] = row[1]
                    log["username"] = row[2]
                    log["host"] = row[3]
                    log["connectionid"] = int(row[4])
                    log["queryid"] = int(row[5])
                    log["operation"] = row[6]
                    log["database"] = row[7]
                    log["object"] = row[8]

                    if log["object"].lower() == "'set autocommit=0'":
                        log["retcode"] = 0
                    else:
                        try:
                            log["retcode"] = int(row[9])
                        except ValueError as e:
                            log["retcode"] = -1
                        except Exception as e:
                            log["retcode"] = -1
                            print(f"{e} : {line}")

                    logger.emit("rds", log)
                except Exception as e:
                    print(f"{e} : {line}")


if __name__ == "__main__":    
    logger = sender.FluentSender(
        "rds", host="0.0.0.0", port=24224, nanosecond_precision=True
    )

    path = "./.raw_data/ffi-krdv-l2alpha-amy-prd-node-mstr/"
    file_list = listdir(path)
    # dir_list = ["audit.log.0.2024-03-18-13-21.2"]

    Parallel(n_jobs=8, prefer="threads")(
        delayed(send_logs)(logger=logger, directory=path, filename=file) for file in file_list
    )
        
    logger.close()
