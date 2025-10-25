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
        return "python:3.10-slim-bullseye"

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
make develop
###ACTION_DELIMITER###
apt-get update && apt-get install -y make
###ACTION_DELIMITER###
make develop
###ACTION_DELIMITER###
pip install numpy
###ACTION_DELIMITER###
pip install multipledispatch python-dateutil tzdata
###ACTION_DELIMITER###
make develop
###ACTION_DELIMITER###
pip install pre-commit
###ACTION_DELIMITER###
make develop
###ACTION_DELIMITER###
make init
###ACTION_DELIMITER###
pip install docker-compose
###ACTION_DELIMITER###
apt-get update && apt-get install -y libyaml-dev gcc
###ACTION_DELIMITER###
pip install docker-compose
###ACTION_DELIMITER###
pip install cython
###ACTION_DELIMITER###
pip install docker-compose
###ACTION_DELIMITER###
pip install PyYAML==5.3.1
###ACTION_DELIMITER###
pip install PyYAML==5.3.1 --only-binary=:all:
###ACTION_DELIMITER###
pip install --upgrade pip
###ACTION_DELIMITER###
pip install docker-compose
###ACTION_DELIMITER###
apt-get update && apt-get install -y docker-compose
###ACTION_DELIMITER###
make init
###ACTION_DELIMITER###
service docker start
###ACTION_DELIMITER###
make init
###ACTION_DELIMITER###
service docker status
###ACTION_DELIMITER###
journalctl -u docker
###ACTION_DELIMITER###
make testlocal
###ACTION_DELIMITER###
pip install pytest
###ACTION_DELIMITER###
make testlocal
###ACTION_DELIMITER###
pip install pytest-xdist
###ACTION_DELIMITER###
make testlocal
###ACTION_DELIMITER###
pip uninstall -y pandas && pip install pandas==1.5.3
###ACTION_DELIMITER###
make testlocal
###ACTION_DELIMITER###
pip uninstall -y numpy && pip install numpy==1.24.4
###ACTION_DELIMITER###
make testlocal
###ACTION_DELIMITER###
pip install sqlalchemy
###ACTION_DELIMITER###
make testlocal
###ACTION_DELIMITER###
pip uninstall -y sqlalchemy && pip install sqlalchemy==1.4.49
###ACTION_DELIMITER###
make testlocal
###ACTION_DELIMITER###
pip uninstall -y sqlalchemy && pip cache purge && pip install sqlalchemy==1.4.49
###ACTION_DELIMITER###
pip uninstall -y sqlalchemy && pip install sqlalchemy==1.3.24
###ACTION_DELIMITER###
make testlocal
###ACTION_DELIMITER###
echo 'pytest -v -n auto -m "not (udf or impala or hdfs or bigquery or mysql or mapd or postgresql or clickhouse)" -k "not test_import_time"' > test_commands.sh
###ACTION_DELIMITER###
echo 'PYTHONHASHSEED="random" pytest -v -n auto -m "not (udf or impala or hdfs or bigquery or mysql or mapd or postgresql or clickhouse)" -k "not test_import_time"' > test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
PYTHONHASHSEED="random" pytest -v -n auto -m "not (udf or impala or hdfs or bigquery or mysql or mapd or postgresql or clickhouse)" -k "not test_import_time"

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
PYTHONHASHSEED="random" pytest -v -n auto -m "not (udf or impala or hdfs or bigquery or mysql or mapd or postgresql or clickhouse)" -k "not test_import_time"

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
PYTHONHASHSEED="random" pytest -v -n auto -m "not (udf or impala or hdfs or bigquery or mysql or mapd or postgresql or clickhouse)" -k "not test_import_time"

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
FROM python:3.10-slim-bullseye

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
RUN git clone https://github.com/ibis-project/ibis.git /home/ibis

WORKDIR /home/ibis
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("ibis-project", "ibis_1848_to_1761")
class IBIS_1848_TO_1761(Instance):
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

        # Define regex pattern to match test status and name
        pattern = re.compile(
            r"\b(PASSED|FAILED|SKIPPED)\b\s+(ibis/.*?)\s*$", re.MULTILINE
        )
        # Find all matches in the log content
        matches = pattern.findall(log)
        # Categorize test names into respective sets
        for status, test_name in matches:
            if status == "PASSED":
                passed_tests.add(test_name)
            elif status == "FAILED":
                failed_tests.add(test_name)
            elif status == "SKIPPED":
                skipped_tests.add(test_name)
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
