# last known versions that have python executables built for windows, may differ from linux
$py27 = "2.7.16"
$py35 = "3.5.4"
$py36 = "3.6.8"
$py37 = "3.7.4"

$VERSIONS = @($py27, $py35, $py36, $py37)
$IMAGE_VERSION="v6"

foreach ($version in $VERSIONS) {
    $major_version = $version.substring(0,1)
    docker build . `
        --no-cache `
        --build-arg PYTHON_VERSION=$version `
        --build-arg PYTHON_MAJOR_VERSION=$major_version `
        --target dagster-integration-image `
        -t "dagster/buildkite-integration:py${version}-windows-${IMAGE_VERSION}"
}