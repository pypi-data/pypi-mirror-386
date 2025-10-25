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
                """grep -A 5 'extras_require' setup.py
###ACTION_DELIMITER###
ls
###ACTION_DELIMITER###
grep -A 5 'extras_require' setup.cfg
###ACTION_DELIMITER###
cat README.unittests.rst
###ACTION_DELIMITER###
cat setup.py
###ACTION_DELIMITER###
cat tox.ini
###ACTION_DELIMITER###
apt-get update
###ACTION_DELIMITER###
cat pyproject.toml
###ACTION_DELIMITER###
pip install pytest>=7.0.0rc1,<8 pytest-xdist
###ACTION_DELIMITER###
pip install "pytest>=7.0.0rc1,<8" pytest-xdist
###ACTION_DELIMITER###
echo 'python -m pytest -v --rootdir . --log-info=sqlalchemy.testing -n4 ./test' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install greenlet
###ACTION_DELIMITER###
bash test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
python -m pytest -v --rootdir . --log-info=sqlalchemy.testing -n4 ./test

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
python -m pytest -v --rootdir . --log-info=sqlalchemy.testing -n4 ./test

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
python -m pytest -v --rootdir . --log-info=sqlalchemy.testing -n4 ./test

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
RUN git clone https://github.com/sqlalchemy/sqlalchemy.git /home/sqlalchemy

WORKDIR /home/sqlalchemy
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("sqlalchemy", "sqlalchemy_7601_to_7443")
class SQLALCHEMY_7601_TO_7443(Instance):
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

        # Implement the log parsing logic here
        # Pattern for passed tests (matches PASSED followed by test path)
        passed_pattern = re.compile(r"PASSED\s+(test/[^ \n]+)", re.MULTILINE)
        passed_tests.update(passed_pattern.findall(log))
        # Pattern for failed tests (matches FAILED followed by test path)
        failed_pattern = re.compile(
            r"(?:\[\s*\d+\]\s*)?(?:\[gw\d+\]\s*\[\s*\d+%\]\s*)?FAILED\s+(test/[^ \n]+)",
            re.MULTILINE,
        )
        failed_tests.update(failed_pattern.findall(log))
        # Patterns for skipped tests (handles worker logs and summary logs)
        skipped_pattern1 = re.compile(
            r"(?:\[\s*\d+\]\s*)?\[gw\d+\]\s*\[\s*\d+%\]\s*SKIPPED\s+([^ \n]+)",
            re.MULTILINE,
        )
        skipped_pattern2 = re.compile(r"SKIPPED \[\d+\] .*?: '(.*?)'")
        skipped_matches = skipped_pattern1.findall(log) + skipped_pattern2.findall(log)
        # Clean up (call) from skipped tests
        cleaned_skipped = []
        for test in skipped_matches:
            cleaned = re.sub(r"\s*\(call\)$", "", test)
            cleaned_skipped.append(cleaned)
        skipped_tests.update(cleaned_skipped)
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
