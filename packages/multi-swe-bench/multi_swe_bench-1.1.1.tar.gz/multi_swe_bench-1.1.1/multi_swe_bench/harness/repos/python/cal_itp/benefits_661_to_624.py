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
        return "ubuntu:22.04"

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
                """apt-get update && apt-get install -y gettext
###ACTION_DELIMITER###
apt-get install -y python3.9 python3.9-pip
###ACTION_DELIMITER###
apt-get install -y python3.9 python3-pip
###ACTION_DELIMITER###
python3.9 -m pip install -r requirements.txt -r tests/pytest/requirements.txt
###ACTION_DELIMITER###
ls /usr/bin/python*
###ACTION_DELIMITER###
apt-get install -y software-properties-common
###ACTION_DELIMITER###
add-apt-repository -y ppa:deadsnakes/ppa
###ACTION_DELIMITER###
apt-get update
###ACTION_DELIMITER###
apt-get install -y python3.9 python3.9-pip
###ACTION_DELIMITER###
apt-get install -y python3.9
###ACTION_DELIMITER###
python3.9 -m ensurepip --upgrade
###ACTION_DELIMITER###
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3.9 get-pip.py
###ACTION_DELIMITER###
apt-get install -y python3.9-distutils
###ACTION_DELIMITER###
python3.9 get-pip.py
###ACTION_DELIMITER###
python3.9 -m pip install -r requirements.txt -r tests/pytest/requirements.txt
###ACTION_DELIMITER###
sed -i 's/requests==2.27.1/requests>=2.31.0/' requirements.txt
###ACTION_DELIMITER###
python3.9 -m pip install -r requirements.txt -r tests/pytest/requirements.txt
###ACTION_DELIMITER###
./bin/init.sh
###ACTION_DELIMITER###
sed -i 's/python/python3.9/g' bin/init.sh
###ACTION_DELIMITER###
./bin/init.sh
###ACTION_DELIMITER###
apt-get install -y libffi-dev && python3.9 -m pip install --force-reinstall cffi
###ACTION_DELIMITER###
./bin/init.sh
###ACTION_DELIMITER###
echo 'pytest -v --cov=benefits --cov-branch --import-mode=importlib' > /home/benefits/test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
pytest -v --cov=benefits --cov-branch --import-mode=importlib

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
pytest -v --cov=benefits --cov-branch --import-mode=importlib

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
pytest -v --cov=benefits --cov-branch --import-mode=importlib

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

# Choose an appropriate base image based on the project's requirements - replace ubuntu:22.04 with actual base image
# For example: FROM ubuntu:**, FROM python:**, FROM node:**, FROM centos:**, etc.
FROM ubuntu:22.04

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
RUN git clone https://github.com/cal-itp/benefits.git /home/benefits

WORKDIR /home/benefits
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("cal-itp", "benefits_661_to_624")
class BENEFITS_661_TO_624(Instance):
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
        passed_tests = set()  # Tests that passed successfully
        failed_tests = set()  # Tests that failed
        skipped_tests = set()  # Tests that were skipped
        import re

        # Define regex patterns
        passed_pattern = re.compile(r"(tests/[\w/]+.py::\w+) PASSED")
        failed_pattern = re.compile(r"FAILED (tests/[\w/]+.py::\w+)")
        skipped_pattern = re.compile(
            r"(tests/[\w/]+.py::\w+) SKIPPED|SKIPPED (tests/[\w/]+.py::\w+)"
        )
        # Extract passed tests
        passed_matches = passed_pattern.findall(log)
        passed_tests.update(passed_matches)
        # Extract failed tests
        failed_matches = failed_pattern.findall(log)
        failed_tests.update(failed_matches)
        # Extract skipped tests
        skipped_matches = skipped_pattern.findall(log)
        for match in skipped_matches:
            for test in match:
                if test:
                    skipped_tests.add(test)
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
