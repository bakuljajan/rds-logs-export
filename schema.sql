CREATE DATABASE IF NOT EXISTS logs;

SET allow_experimental_inverted_index = true;
SET allow_experimental_object_type = 1;

CREATE TABLE logs.rds_audit_logs
(
    `timestamp` DateTime64(6, 'Asia/Jakarta') CODEC(DoubleDelta, ZSTD),
    `serverhost` LowCardinality(String) CODEC(ZSTD),
    `username` LowCardinality(String) CODEC(ZSTD),
    `host` String DEFAULT '' CODEC(ZSTD),
    `connectionid` UInt64 CODEC(T64, ZSTD),
    `queryid` UInt64 CODEC(T64, ZSTD),
    `operation` LowCardinality(String) CODEC(ZSTD),
    `database` LowCardinality(String) CODEC(ZSTD),
    `object` String CODEC(ZSTD),
    `retcode` Int8 CODEC(T64, ZSTD),
)
ENGINE = ReplacingMergeTree()
ORDER BY (timestamp, serverhost, username, host, connectionid, queryid, operation, database)
PARTITION BY toYYYYMMDD(`timestamp`);

ALTER TABLE logs.rds_audit_logs ADD INDEX inv_idx(lower(object)) TYPE full_text();
ALTER TABLE logs.rds_audit_logs MATERIALIZE INDEX inv_idx;
