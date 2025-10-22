# FRED-OGD: SOURCE: BANXICO

FRED's official open-sourced governed datasets derived from the `BANXICO` source.
* Bucket Name: `fred-ogd-source-banxico`

## About this source

`BANXICO` (Banco de México) is Mexico's central bank, providing authoritative financial and economic data. This source enables automated, recurrent downloads of time-series datasets such as Mexican interest rates, exchange rates (e.g., USD/MXN FIX), CETES yields, and other key indicators. These snapshots support analysis and integration into data-driven workflows.

All available series:
```commandline
$ fred-ogd execute banxico timeseries
```

## Layer: Landing

The landing layer can be executed at a per-series basis by calling the `banxico landing` command as following:

```commandline
$ fred-ogd execute banxico landing --timeserie USD_MXN
```
* You can optionally provide a `backend` argument (default: `FRDOGD_BACKEND_SERVICE`).

Consider that the backend service attempt to auto-configure. This requires having all the required
environment variables setup. For MinIO:
* `MINIO_ACCESS_KEY`
* `MINIO_SECRET_KEY`
* `MINIO_ENDPOINT`
* (Optional) `MINIO_BUCKET` the backend will use `FRDOGD_SOURCE_FULLNAME` (i.e., `fred-ogd-source-banxico`) by default.
