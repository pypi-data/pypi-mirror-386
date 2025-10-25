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
pip install -e .
###ACTION_DELIMITER###
pytest -v --cov-config=pyproject.toml --cov=scrapy --cov-report=xml --cov-report= --durations=10 docs scrapy tests --doctest-modules
###ACTION_DELIMITER###
pip install -e '.[test]'
###ACTION_DELIMITER###
pip install attrs coverage>=7.4.0 pexpect>=4.8.0 pyftpdlib>=2.0.1 pygments 'pytest!=8.2.*' pytest-cov>=4.0.0 pytest-xdist 'sybil>=1.3.0' testfixtures
###ACTION_DELIMITER###
pytest --version
###ACTION_DELIMITER###
pytest -v --cov-config=pyproject.toml --cov=scrapy --cov-report=xml --cov-report= --durations=10 docs scrapy tests --doctest-modules
###ACTION_DELIMITER###
echo 'pytest -v --cov-config=pyproject.toml --cov=scrapy --cov-report=xml --cov-report= --durations=10 docs scrapy tests --doctest-modules' > test_commands.sh
###ACTION_DELIMITER###
cat test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
pytest -v --cov-config=pyproject.toml --cov=scrapy --cov-report=xml --cov-report= --durations=10 docs scrapy tests --doctest-modules

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
pytest -v --cov-config=pyproject.toml --cov=scrapy --cov-report=xml --cov-report= --durations=10 docs scrapy tests --doctest-modules

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
pytest -v --cov-config=pyproject.toml --cov=scrapy --cov-report=xml --cov-report= --durations=10 docs scrapy tests --doctest-modules

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
RUN git clone https://github.com/scrapy/scrapy.git /home/scrapy

WORKDIR /home/scrapy
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("scrapy", "scrapy_6618_to_6542")
class SCRAPY_6618_TO_6542(Instance):
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
        passed_tests = set()  # type: set[str]
        failed_tests = set()  # type: set[str]
        skipped_tests = set()  # type: set[str]
        import re

        # Regex patterns to match test lines
        # Pattern 1: Test name followed by status and percentage (e.g., "test_name PASSED [  0%]")
        pattern1 = re.compile(
            r"^(.*?)\s+(PASSED|FAILED|SKIPPED|XFAIL)\s+\[\s*\d+%\s*\]$"
        )
        # Pattern 2: Status followed by test name (e.g., "FAILED test_name")
        pattern2 = re.compile(r"^(PASSED|FAILED|SKIPPED|XFAIL)\s+(.*)$")
        for line in log.split("\n"):
            line = line.strip()
            if not line:
                continue
            match1 = pattern1.match(line)
            match2 = pattern2.match(line)
            test_name = None
            status = None
            if match1:
                test_name = match1.group(1).strip()
                status = match1.group(2)
            elif match2:
                status = match2.group(1)
                test_name = match2.group(2).strip()
            else:
                continue  # Not a test line
            # Remove any trailing error messages after ' - '
            if " - " in test_name:
                test_name = test_name.split(" - ")[0].strip()
            # Categorize the test based on status
            if status == "PASSED":
                passed_tests.add(test_name)
            elif status == "FAILED":
                failed_tests.add(test_name)
            elif status == "SKIPPED":
                skipped_tests.add(test_name)
            # XFAIL is not mapped to any of the required categories; consider handling if needed
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
