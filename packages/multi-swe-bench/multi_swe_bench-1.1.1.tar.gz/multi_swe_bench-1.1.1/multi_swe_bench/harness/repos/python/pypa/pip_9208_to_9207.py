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
apt-get update && apt-get install -y build-essential libssl-dev libffi-dev
###ACTION_DELIMITER###
pip install nox
###ACTION_DELIMITER###
nox -s test-3.9
###ACTION_DELIMITER###
pip install -r tests/requirements.txt
###ACTION_DELIMITER###
pip uninstall -r tests/requirements.txt -y
###ACTION_DELIMITER###
nox -s test-3.9
###ACTION_DELIMITER###
echo 'pytest -v' > test_commands.sh
###ACTION_DELIMITER###
echo -e 'pip install -r tests/requirements.txt
python setup.py sdist
pip install dist/*.tar.gz
pytest -v' > test_commands.sh
###ACTION_DELIMITER###
echo 'pytest -v' > test_commands.sh
###ACTION_DELIMITER###
pip install pytest-mock
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install setuptools
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install -r tests/requirements.txt
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install -e .
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
python -c 'import shutil, sys; shutil.rmtree(sys.argv[1], ignore_errors=True)' tests/data/common_wheels && pip wheel -w tests/data/common_wheels -r tests/requirements-common_wheels.txt
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo -e 'python tools/tox_pip.py install -r tests/requirements.txt
python tools/tox_pip.py install -e .
pytest -v' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo -e 'python -m venv .venv
. .venv/bin/activate
python tools/tox_pip.py install -r tests/requirements.txt
python tools/tox_pip.py install -e .
pytest -v' > test_commands.sh
###ACTION_DELIMITER###
echo 'pytest -v' > test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
pytest -v

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
pytest -v

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
pytest -v

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
RUN git clone https://github.com/pypa/pip.git /home/pip

WORKDIR /home/pip
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("pypa", "pip_9208_to_9207")
class PIP_9208_TO_9207(Instance):
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
        import json  # Note: json is imported but not used; may be removed if unnecessary

        # Remove ANSI escape codes from the log content
        log_clean = re.sub(r"\x1b\[[0-9;]*m", "", log)
        # Regular expressions to match test lines with status
        pattern_test_before_status = (
            r"^(tests/.*?)\s+(PASSED|FAILED|ERROR|SKIPPED|XFAILED|XPASSED)\b"
        )
        pattern_status_before_test = (
            r"^(PASSED|FAILED|ERROR|SKIPPED|XFAILED|XPASSED)\s+(tests/.*?)\b"
        )
        for line in log_clean.split("\n"):
            line = line.strip()
            # Check if the line matches test name before status
            match = re.match(pattern_test_before_status, line)
            if match:
                test_name = match.group(1).strip()
                status = match.group(2).strip()
            else:
                # Check if the line matches status before test name
                match = re.match(pattern_status_before_test, line)
                if match:
                    status = match.group(1).strip()
                    test_name = match.group(2).strip()
                else:
                    continue  # Skip lines that don't match test patterns
            # Categorize the test based on its status
            if status in ("PASSED", "XPASSED"):
                passed_tests.add(test_name)
            elif status in ("FAILED", "ERROR", "XFAILED"):
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
