## dagster-dask

Check out the docs for `dagster-dask` in the [deployment section](https://dagster.readthedocs.io/en/latest/sections/deploying/deploying.html) of Dagster's docs.

### Running tests

You will need a running Dask cluster:

    export PYTHON_VERSION=3.6
    ./dagster_dask_tests/dask-docker/build.sh $PYTHON_VERSION
    docker-compose -f dagster_dask_tests/dask-docker/docker-compose.yml up -d
