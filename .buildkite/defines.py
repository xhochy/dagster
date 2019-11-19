# This should be an enum once we make our own buildkite AMI with py3
class SupportedPython:
    V3_7 = "3.7.4"
    V3_6 = "3.6.9"
    V3_5 = "3.5.7"
    V2_7 = "2.7.16"


SupportedPythons = [
    SupportedPython.V3_7,
    SupportedPython.V3_6,
    SupportedPython.V3_5,
    SupportedPython.V2_7,
]

# TODO: Build python from source instead of relying on built-in installers so we can keep the
# versions of Python in sync (https://github.com/dagster-io/dagster/issues/1923)
class WindowsSupportedPython:
    V3_7 = "3.7.4"
    V3_6 = "3.6.8"
    V3_5 = "3.5.4"
    V2_7 = "2.7.16"


WindowsSupportedPythons = [
    WindowsSupportedPython.V3_7,
    WindowsSupportedPython.V3_6,
    WindowsSupportedPython.V3_5,
    WindowsSupportedPython.V2_7,
]
WindowsSupportedPythonMap = {
    SupportedPython.V3_7: "3.7.4",
    SupportedPython.V3_6: "3.6.8",
    SupportedPython.V3_5: "3.5.4",
    SupportedPython.V2_7: "2.7.16",
}

SupportedPython3s = [SupportedPython.V3_7, SupportedPython.V3_6, SupportedPython.V3_5]
