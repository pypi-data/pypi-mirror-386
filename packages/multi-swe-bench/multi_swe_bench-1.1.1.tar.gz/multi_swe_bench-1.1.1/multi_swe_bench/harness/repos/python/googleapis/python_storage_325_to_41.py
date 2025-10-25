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
        return "python:3.10-slim"

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
                """ls
###ACTION_DELIMITER###
pip install --upgrade pip
###ACTION_DELIMITER###
pip install -e .
###ACTION_DELIMITER###
pip install mock pytest pytest-cov
###ACTION_DELIMITER###
echo 'pytest --no-header -rA --tb=no -p no:cacheprovider -v tests/' > test_commands.sh
###ACTION_DELIMITER###
cat test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo 'pytest --no-header -rA --tb=no -p no:cacheprovider -v tests/unit/' > test_commands.sh
###ACTION_DELIMITER###
cat test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install pytz
###ACTION_DELIMITER###
echo 'nox -s unit' > test_commands.sh
###ACTION_DELIMITER###
cat test_commands.sh
###ACTION_DELIMITER###
pip install nox
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo 'GOOGLE_APPLICATION_CREDENTIALS=/dev/null pytest --no-header -rA --tb=no -p no:cacheprovider -v tests/unit/' > test_commands.sh
###ACTION_DELIMITER###
cat test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo 'GOOGLE_AUTH_DISABLED=1 GOOGLE_CLOUD_PROJECT=test-project pytest --no-header -rA --tb=no -p no:cacheprovider -v tests/unit/' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo -e 'import pytest
from unittest.mock import Mock

@pytest.fixture(autouse=True)
def mock_google_auth(mocker):
    mock_credentials = Mock()
    mocker.patch("google.auth.default", return_value=(mock_credentials, "PROJECT"))' > tests/unit/conftest.py
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install pytest-mock
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo 'GOOGLE_AUTH_DISABLED=1 pytest --no-header -rA --tb=no -p no:cacheprovider -v tests/unit/' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
GOOGLE_AUTH_DISABLED=1 pytest --no-header -rA --tb=no -p no:cacheprovider -v tests/unit/

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
GOOGLE_AUTH_DISABLED=1 pytest --no-header -rA --tb=no -p no:cacheprovider -v tests/unit/

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
GOOGLE_AUTH_DISABLED=1 pytest --no-header -rA --tb=no -p no:cacheprovider -v tests/unit/

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
FROM python:3.10-slim

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
RUN git clone https://github.com/googleapis/python-storage.git /home/python-storage

WORKDIR /home/python-storage
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("googleapis", "python_storage_325_to_41")
class PYTHON_STORAGE_325_TO_41(Instance):
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
        passed_tests: set[str] = set()
        failed_tests: set[str] = set()
        skipped_tests: set[str] = set()
        import re

        # Refined regex patterns to handle test status formats
        # Matches both: [line] test_name PASSED [percent] and [line] PASSED test_name
        pattern_passed_failed = r"(tests/unit/.*?\.py::[^\s]+)\s+(PASSED|FAILED)|(PASSED|FAILED)\s+(tests/unit/.*?\.py::[^\s]+)"
        # Matches SKIPPED tests with file:line (log does not provide full test name)
        pattern_skipped = r"SKIPPED\s+\[\d+\]\s+(tests/unit/[^:]+\.py:\d+)"  # Captures file:line for skipped
        # Extract and process PASSED/FAILED tests
        for match in re.findall(pattern_passed_failed, log):
            test1, status1, status2, test2 = match
            if status1:
                test, status = test1, status1
            else:
                test, status = test2, status2
            if status == "PASSED":
                passed_tests.add(test)
            elif status == "FAILED":
                failed_tests.add(test)
        # Extract and process SKIPPED tests
        skipped_tests.update(re.findall(pattern_skipped, log))
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
