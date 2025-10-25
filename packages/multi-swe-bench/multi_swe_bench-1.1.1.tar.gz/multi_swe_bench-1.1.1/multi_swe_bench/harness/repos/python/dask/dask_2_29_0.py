import re
from typing import Optional

from multi_swe_bench.harness.image import Config, File, Image
from multi_swe_bench.harness.instance import Instance, TestResult
from multi_swe_bench.harness.pull_request import PullRequest


class ImageDefault(Image):
    def __init__(self, pr: PullRequest, config: Config):
        self._pr = pr
        self._config = config

    @property
    def pr(self) -> PullRequest:
        return self._pr

    @property
    def config(self) -> Config:
        return self._config

    def dependency(self) -> str:
        return "python:3.8-slim"

    def image_prefix(self) -> str:
        return "envagent"

    def image_tag(self) -> str:
        return f"pr-{self.pr.number}"

    def workdir(self) -> str:
        return f"pr-{self.pr.number}"

    def files(self) -> list[File]:
        return [
            File(
                ".",
                "fix.patch",
                f"{self.pr.fix_patch}",
            ),
            File(
                ".",
                "test.patch",
                f"{self.pr.test_patch}",
            ),
            File(
                ".",
                "prepare.sh",
                """ls -la
###ACTION_DELIMITER###
which conda
###ACTION_DELIMITER###
python3.8 --version
###ACTION_DELIMITER###
python3.8 -m pip install --upgrade pip
###ACTION_DELIMITER###
python3.8 -m pip install numpy==1.17.* pandas==1.0.* pytest pytest-xdist moto>=1.3.14 flask fastparquet h5py tables zarr tiledb fsspec>=0.6.0 sqlalchemy pyarrow>=0.14.0 coverage jsonschema bcolz blosc boto3 botocore bokeh httpretty aiohttp chest s3fs cloudpickle crick cytoolz distributed graphviz ipython lz4 numba partd psutil requests scikit-image scikit-learn scipy toolz python-snappy sparse cachey graphviz pandas-datareader xxhash mmh3 cityhash
###ACTION_DELIMITER###
apt-get update && apt-get install -y build-essential python3.8-dev libsnappy-dev liblz4-dev libblosc-dev libhdf5-dev libzstd-dev libtiledb-dev graphviz
###ACTION_DELIMITER###
python3.8 -m pip install numpy==1.17.* pandas==1.0.* pytest pytest-xdist moto>=1.3.14 flask fastparquet h5py tables zarr tiledb fsspec>=0.6.0 sqlalchemy pyarrow>=0.14.0 coverage jsonschema bcolz blosc boto3 botocore bokeh httpretty aiohttp chest s3fs cloudpickle crick cytoolz distributed graphviz ipython lz4 numba partd psutil requests scikit-image scikit-learn scipy toolz python-snappy sparse cachey graphviz pandas-datareader xxhash mmh3 cityhash
###ACTION_DELIMITER###
python3.8 -m pip install --upgrade cython wheel
###ACTION_DELIMITER###
python3.8 -m pip install bcolz fastparquet
###ACTION_DELIMITER###
python3.8 -m pip install numpy==1.17.* pandas==1.0.* pytest pytest-xdist moto>=1.3.14 flask h5py tables zarr tiledb fsspec>=0.6.0 sqlalchemy pyarrow>=0.14.0 coverage jsonschema blosc boto3 botocore bokeh httpretty aiohttp chest s3fs cloudpickle crick cytoolz distributed graphviz ipython lz4 numba partd psutil requests scikit-image scikit-learn scipy toolz python-snappy sparse cachey graphviz pandas-datareader xxhash mmh3 cityhash
###ACTION_DELIMITER###
python3.8 -m pip install --no-deps -e .[complete]
###ACTION_DELIMITER###
echo 'pytest dask --runslow -n3 --no-header -rA --tb=no -p no:cacheprovider' > /home/dask/test_commands.sh && chmod +x /home/dask/test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
pytest dask --runslow -n3 --no-header -rA --tb=no -p no:cacheprovider

""".format(pr=self.pr),
            ),
            File(
                ".",
                "test-run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
if ! git -C /home/{pr.repo} apply --whitespace=nowarn /home/test.patch; then
    echo "Error: git apply failed" >&2
    exit 1  
fi
pytest dask --runslow -n3 --no-header -rA --tb=no -p no:cacheprovider

""".format(pr=self.pr),
            ),
            File(
                ".",
                "fix-run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
if ! git -C /home/{pr.repo} apply --whitespace=nowarn  /home/test.patch /home/fix.patch; then
    echo "Error: git apply failed" >&2
    exit 1  
fi
pytest dask --runslow -n3 --no-header -rA --tb=no -p no:cacheprovider

""".format(pr=self.pr),
            ),
        ]

    def dockerfile(self) -> str:
        copy_commands = ""
        for file in self.files():
            copy_commands += f"COPY {file.name} /home/\n"

        dockerfile_content = """
# This is a template for creating a Dockerfile to test patches
# LLM should fill in the appropriate values based on the context

# Choose an appropriate base image based on the project's requirements - replace [base image] with actual base image
# For example: FROM ubuntu:**, FROM python:**, FROM node:**, FROM centos:**, etc.
FROM python:3.8-slim

## Set noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# Install basic requirements
# For example: RUN apt-get update && apt-get install -y git
# For example: RUN yum install -y git
# For example: RUN apk add --no-cache git
RUN apt-get update && apt-get install -y git

# Ensure bash is available
RUN if [ ! -f /bin/bash ]; then         if command -v apk >/dev/null 2>&1; then             apk add --no-cache bash;         elif command -v apt-get >/dev/null 2>&1; then             apt-get update && apt-get install -y bash;         elif command -v yum >/dev/null 2>&1; then             yum install -y bash;         else             exit 1;         fi     fi

WORKDIR /home/
COPY fix.patch /home/
COPY test.patch /home/
RUN git clone https://github.com/dask/dask.git /home/dask

WORKDIR /home/dask
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("dask", "dask_2_29_0")
class DASK_2_29_0(Instance):
    def __init__(self, pr: PullRequest, config: Config, *args, **kwargs):
        super().__init__()
        self._pr = pr
        self._config = config

    @property
    def pr(self) -> PullRequest:
        return self._pr

    def dependency(self) -> Optional[Image]:
        return ImageDefault(self.pr, self._config)

    def run(self, run_cmd: str = "") -> str:
        if run_cmd:
            return run_cmd

        return "bash /home/run.sh"

    def test_patch_run(self, test_patch_run_cmd: str = "") -> str:
        if test_patch_run_cmd:
            return test_patch_run_cmd

        return "bash /home/test-run.sh"

    def fix_patch_run(self, fix_patch_run_cmd: str = "") -> str:
        if fix_patch_run_cmd:
            return fix_patch_run_cmd

        return "bash /home/fix-run.sh"

    def parse_log(self, log: str) -> TestResult:
        # Parse the log content and extract test execution results.
        passed_tests = set()
        failed_tests = set()
        skipped_tests = set()
        # Implement the log parsing logic here
        # Regex patterns for PASSED, FAILED, SKIPPED
        passed_pattern = re.compile(r"^PASSED ([^\s].*?)(?:\s-.*)?$", re.MULTILINE)
        failed_pattern = re.compile(r"^FAILED ([^\s].*?)(?:\s-.*)?$", re.MULTILINE)
        skipped_pattern = re.compile(r"^SKIPPED \[\d+\] ([^:]+:\d+)", re.MULTILINE)
        passed_tests.update(passed_pattern.findall(log))
        failed_tests.update(failed_pattern.findall(log))
        skipped_tests.update(skipped_pattern.findall(log))

        return TestResult(
            passed_count=len(passed_tests),
            failed_count=len(failed_tests),
            skipped_count=len(skipped_tests),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
        )
