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
ls docs
###ACTION_DELIMITER###
make install-dev
###ACTION_DELIMITER###
apt-get update && apt-get install -y make
###ACTION_DELIMITER###
make install-dev
###ACTION_DELIMITER###
git submodule update --init --recursive
###ACTION_DELIMITER###
make install-dev
###ACTION_DELIMITER###
apt-get update && apt-get install -y nodejs npm
###ACTION_DELIMITER###
make install-dev
###ACTION_DELIMITER###
make cythonize
###ACTION_DELIMITER###
cython -3 -o aiohttp/_websocket/reader_c.c aiohttp/_websocket/reader_c.pyx -I aiohttp -Werror
###ACTION_DELIMITER###
ls aiohttp/_websocket
###ACTION_DELIMITER###
cython -3 -o aiohttp/_websocket/reader_c.c aiohttp/_websocket/reader_c.py -I aiohttp -Werror
###ACTION_DELIMITER###
make install-dev
###ACTION_DELIMITER###
make vtest
###ACTION_DELIMITER###
echo -e 'pytest -s -v
python -X dev -m pytest --cov-append -s -v -m dev_mode' > test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
pytest -s -v
python -X dev -m pytest --cov-append -s -v -m dev_mode

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
pytest -s -v
python -X dev -m pytest --cov-append -s -v -m dev_mode

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
pytest -s -v
python -X dev -m pytest --cov-append -s -v -m dev_mode

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
RUN git clone https://github.com/aio-libs/aiohttp.git /home/aiohttp

WORKDIR /home/aiohttp
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("aio-libs", "aiohttp_9530_to_9016")
class AIOHTTP_9530_TO_9016(Instance):
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
        import json

        # Compile regex patterns to match test cases and their statuses
        test_status_pattern = re.compile(
            r"(tests/[^\s]+)\s+(PASSED|XFAIL|FAILED|SKIPPED)"
        )
        status_test_pattern = re.compile(
            r"(PASSED|XFAIL|FAILED|SKIPPED)\s+(tests/[^\s]+)"
        )
        # Split log into lines and process each line
        for line in log.split("\n"):
            # Check for test name followed by status (e.g., "tests/...::test_name PASSED")
            match = test_status_pattern.search(line)
            if match:
                test_name = match.group(1)
                status = match.group(2)
            else:
                # Check for status followed by test name (e.g., "XFAIL tests/...::test_name")
                match = status_test_pattern.search(line)
                if match:
                    status = match.group(1)
                    test_name = match.group(2)
                else:
                    continue  # No test case found in this line
            # Categorize the test based on its status
            if status == "PASSED":
                passed_tests.add(test_name)
            elif status in ("XFAIL", "FAILED"):
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
