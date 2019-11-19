# last known versions that have python executables built for windows, may differ from linux
$py27 = "2.7.16"
$py35 = "3.5.4"
$py36 = "3.6.8"
$py37 = "3.7.4"

$VERSIONS = @($py27, $py35, $py36, $py37)
$AWS_ACCOUNT_ID=$env:AWS_ACCOUNT_ID
$IMAGE_VERSION="v6"

foreach ($version in $VERSIONS) {
    $name = ("{0}{1}" -f $version.substring(0,1), $version.substring(2,1))
    docker tag "dagster/buildkite-integration:py${name}-windows-${IMAGE_VERSION}" `
        "${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com/buildkite-integration:py${name}-windows-${IMAGE_VERSION}"

    docker push "${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com/buildkite-integration:py${name}-windows-${IMAGE_VERSION}"
}