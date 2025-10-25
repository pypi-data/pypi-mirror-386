from deps_rocker.simple_rocker_extension import SimpleRockerExtension


class Curl(SimpleRockerExtension):
    """Adds curl to your docker container"""

    name = "curl"
    apt_packages = ["curl", "ca-certificates"]
