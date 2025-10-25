import re
import json
from typing import Optional, Union

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
        return "python:3.9-slim"

    def image_prefix(self) -> str:
        return "envagent"

    def image_tag(self) -> str:
        return f"pr-{self.pr.number}"

    def workdir(self) -> str:
        return f"pr-{self.pr.number}"

    def files(self) -> list[File]:
        repo_name = self.pr.repo
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
                """apt-get update
###ACTION_DELIMITER###
apt-get install -y libgdal-dev gdal-bin libproj-dev
###ACTION_DELIMITER###
gdal-config --version
###ACTION_DELIMITER###
pip install GDAL==3.6.2
###ACTION_DELIMITER###
apt-get install -y g++
###ACTION_DELIMITER###
pip install GDAL==3.6.2
###ACTION_DELIMITER###
pip install --upgrade pip && pip install -r requirements.txt -r requirements-dev.txt
###ACTION_DELIMITER###
echo 'pytest -v --import-mode=importlib --durations=0 tests' > test_commands.sh
###ACTION_DELIMITER###
cat test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install -e .
###ACTION_DELIMITER###
pip install --force-reinstall GDAL==3.6.2
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip uninstall -y GDAL && pip install GDAL==3.6.2 --no-binary :all:
###ACTION_DELIMITER###
pip install --upgrade numpy && pip install GDAL==3.6.2 --no-binary :all: -v
###ACTION_DELIMITER###
pip cache purge && pip uninstall -y GDAL && pip install GDAL==3.6.2 --no-binary :all: -v
###ACTION_DELIMITER###
export CFLAGS="-I$(python -c 'import numpy; print(numpy.get_include())')" && pip uninstall -y GDAL && pip install GDAL==3.6.2 --no-binary :all: -v
###ACTION_DELIMITER###
ls /usr/local/lib/python3.9/site-packages/osgeo/ | grep _gdal_array
###ACTION_DELIMITER###
ls -l /usr/local/lib/python3.9/site-packages/osgeo/_gdal_array.cpython-39-x86_64-linux-gnu.so
###ACTION_DELIMITER###
ldd /usr/local/lib/python3.9/site-packages/osgeo/_gdal_array.cpython-39-x86_64-linux-gnu.so
###ACTION_DELIMITER###
python -c 'import sys; from osgeo import _gdal_array; print("Import successful")' 2>&1
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
git submodule update --init --recursive
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
ls -la data && cat .gitmodules 2>/dev/null
###ACTION_DELIMITER###
cat README.md 2>/dev/null || echo 'README not found'
###ACTION_DELIMITER###
git clone https://github.com/natcap/invest-test-data.git data/invest-test-data
###ACTION_DELIMITER###
git clone --depth 1 https://github.com/natcap/invest-test-data.git data/invest-test-data
###ACTION_DELIMITER###
wget -q https://github.com/natcap/invest-test-data/archive/refs/heads/main.zip -O test-data.zip && unzip -q test-data.zip -d data && mv data/invest-test-data-main data/invest-test-data && rm test-data.zip
###ACTION_DELIMITER###
apt-get install -y wget
###ACTION_DELIMITER###
wget -q https://github.com/natcap/invest-test-data/archive/refs/heads/main.zip -O test-data.zip && unzip -q test-data.zip -d data && mv data/invest-test-data-main data/invest-test-data && rm test-data.zip
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
ls -la data/invest-test-data && ls -la data/invest-test-data/wind_energy/input 2>/dev/null || echo 'Wind energy input files not found'
###ACTION_DELIMITER###
ls -la data
###ACTION_DELIMITER###
rm -rf data && mkdir -p data && wget -v https://github.com/natcap/invest-test-data/archive/refs/heads/main.zip -O data/test-data.zip && unzip -v data/test-data.zip -d data && mv data/invest-test-data-main data/invest-test-data && rm data/test-data.zip
###ACTION_DELIMITER###
rm -rf data && mkdir -p data && wget -v https://github.com/natcap/invest-test-data/archive/main.zip -O data/test-data.zip && unzip -v data/test-data.zip -d data && mv data/invest-test-data-main data/invest-test-data && rm data/test-data.zip""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
pytest -v --import-mode=importlib --durations=0 tests

""".replace("[[REPO_NAME]]", repo_name),
            ),
            File(
                ".",
                "test-run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
if ! git -C /home/[[REPO_NAME]] apply --whitespace=nowarn /home/test.patch; then
    echo "Error: git apply failed" >&2
    exit 1  
fi
pytest -v --import-mode=importlib --durations=0 tests

""".replace("[[REPO_NAME]]", repo_name),
            ),
            File(
                ".",
                "fix-run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
if ! git -C /home/[[REPO_NAME]] apply --whitespace=nowarn  /home/test.patch /home/fix.patch; then
    echo "Error: git apply failed" >&2
    exit 1  
fi
pytest -v --import-mode=importlib --durations=0 tests

""".replace("[[REPO_NAME]]", repo_name),
            ),
        ]

    def dockerfile(self) -> str:
        copy_commands = ""
        for file in self.files():
            copy_commands += f"COPY {file.name} /home/\n"

        dockerfile_content = """
# This is a template for creating a Dockerfile to test patches
# LLM should fill in the appropriate values based on the context

# Choose an appropriate base image based on the project's requirements - replace python:3.9-slim with actual base image
# For example: FROM ubuntu:**, FROM python:**, FROM node:**, FROM centos:**, etc.
FROM python:3.9-slim

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
RUN git clone https://github.com/natcap/invest.git /home/invest

WORKDIR /home/invest
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("natcap", "invest_1247_to_1222")
class INVEST_1247_TO_1222(Instance):
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
        passed_tests: set[str] = set()  # Tests that passed successfully
        failed_tests: set[str] = set()  # Tests that failed
        skipped_tests: set[str] = set()  # Tests that were skipped
        import re

        # Regex patterns to match test lines
        # Updated patterns to handle optional parentheses, colons, and percentage indicators
        # More flexible patterns to handle varied whitespace and trailing content
        pattern1 = re.compile(
            r"^\s*(tests/[^:]+::[^:]+::test_\w+)\s+(PASSED|FAILED|SKIPPED)\b.*$"
        )
        pattern2 = re.compile(
            r"^\s*(PASSED|FAILED|SKIPPED)\b.*?(tests/[^:]+::[^:]+::test_\w+)\b.*$"
        )
        for line in log.split("\n"):
            line = line.strip()
            # Check pattern 1: test name followed by status
            match = pattern1.match(line)
            if match:
                test_name = match.group(1)
                status = match.group(2)
                if status == "PASSED":
                    passed_tests.add(test_name)
                elif status == "FAILED":
                    failed_tests.add(test_name)
                elif status == "SKIPPED":
                    skipped_tests.add(test_name)
                continue
            # Check pattern 2: status followed by test name
            match = pattern2.match(line)
            if match:
                status = match.group(1)
                test_name = match.group(2)
                if status == "PASSED":
                    passed_tests.add(test_name)
                elif status == "FAILED":
                    failed_tests.add(test_name)
                elif status == "SKIPPED":
                    skipped_tests.add(test_name)
                continue
        parsed_results = {
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
        }

        return TestResult(
            passed_count=len(passed_tests),
            failed_count=len(failed_tests),
            skipped_count=len(skipped_tests),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
        )
