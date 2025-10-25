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
        return "fedora:31"

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
                """ls
###ACTION_DELIMITER###
dnf builddep -y packit.spec
###ACTION_DELIMITER###
dnf install -y 'dnf-command(builddep)'
###ACTION_DELIMITER###
dnf builddep -y packit.spec
###ACTION_DELIMITER###
pip3 install -e .
###ACTION_DELIMITER###
echo 'PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 pytest -v ./tests/unit ./tests/integration ./tests/functional' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip3 list | grep pytest
###ACTION_DELIMITER###
pip3 install pytest
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip3 install flexmock
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip3 uninstall -y flexmock && pip3 install flexmock==0.10.4
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
git config --global user.name "Test User" && git config --global user.email "test@example.com"
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
dnf install -y make rpm-build""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 pytest -v ./tests/unit ./tests/integration ./tests/functional

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
PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 pytest -v ./tests/unit ./tests/integration ./tests/functional

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
PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 pytest -v ./tests/unit ./tests/integration ./tests/functional

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

# Choose an appropriate base image based on the project's requirements - replace [base image] with actual base image
# For example: FROM ubuntu:**, FROM python:**, FROM node:**, FROM centos:**, etc.
FROM fedora:31

## Set noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# Install basic requirements
# For example: RUN apt-get update && apt-get install -y git
# For example: RUN yum install -y git
# For example: RUN apk add --no-cache git
RUN dnf install -y git

# Ensure bash is available
RUN if [ ! -f /bin/bash ]; then         if command -v apk >/dev/null 2>&1; then             apk add --no-cache bash;         elif command -v apt-get >/dev/null 2>&1; then             apt-get update && apt-get install -y bash;         elif command -v yum >/dev/null 2>&1; then             yum install -y bash;         else             exit 1;         fi     fi

WORKDIR /home/
COPY fix.patch /home/
COPY test.patch /home/
RUN git clone https://github.com/packit/packit.git /home/packit

WORKDIR /home/packit
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("packit", "packit_999_to_596")
class PACKIT_999_TO_596(Instance):
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
        # Pattern 1: Test name followed by status and percentage (e.g., "tests/... PASSED [  0%]")
        pattern1 = re.compile(
            r"^(tests/.*?\.py::.*?) (PASSED|FAILED|SKIPPED) \[\s*\d+%\]$"
        )
        # Pattern 2: Status followed by test name (e.g., "FAILED tests/...")
        pattern2 = re.compile(r"^(PASSED|FAILED|SKIPPED) (tests/.*?\.py::.*)$")
        for line in log.split("\n"):
            line = line.strip()
            # Check pattern 1
            match = pattern1.match(line)
            if match:
                test_name = match.group(1)
                status = match.group(2)
            else:
                # Check pattern 2
                match = pattern2.match(line)
                if match:
                    status = match.group(1)
                    test_name = match.group(2)
                else:
                    continue  # No match, skip line
            # Add to the appropriate set
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
