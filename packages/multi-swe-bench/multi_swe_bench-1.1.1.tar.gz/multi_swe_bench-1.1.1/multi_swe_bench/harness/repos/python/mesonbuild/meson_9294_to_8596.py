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
        return "python:3.11-slim"

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
ninja --version
###ACTION_DELIMITER###
python3 -m pip install ninja
###ACTION_DELIMITER###
python3 -m pip install -e .
###ACTION_DELIMITER###
echo 'python3 run_tests.py --verbose' > test_commands.sh
###ACTION_DELIMITER###
cat test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo 'python3 run_tests.py' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
apt-get update && apt-get install -y gcc
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
apt-get update && apt-get install -y g++
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
apt-get update && apt-get install -y pkg-config
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
apt-get update && apt-get install -y zlib1g-dev
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
apt-get update && apt-get install -y libglib2.0-dev
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
python3 run_tests.py --help""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
python3 run_tests.py

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
python3 run_tests.py

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
python3 run_tests.py

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
FROM python:3.11-slim

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
RUN git clone https://github.com/mesonbuild/meson.git /home/meson

WORKDIR /home/meson
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("mesonbuild", "meson_9294_to_8596")
class MESON_9294_TO_8596(Instance):
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
        passed_tests = set[str]()  # Tests that passed successfully
        failed_tests = set[str]()  # Tests that failed
        skipped_tests = set[str]()  # Tests that were skipped
        import re

        # Parse unittest-style tests (handles multi-line entries with warnings)
        lines = log.split("\n")
        current_test = None
        for line in lines:
            line_strip = line.strip()
            # Track test name and check for same-line status
            if (
                not current_test
                and "..." in line_strip
                and "(" in line_strip
                and ")" in line_strip
            ):
                parts = line_strip.split("...", 1)
                test_part = parts[0].strip()
                if test_part.startswith("test_"):
                    current_test = test_part
                    # Check if status is in the same line
                    if len(parts) > 1:
                        after_part = parts[1].strip().lower()
                        if any(
                            after_part.startswith(s)
                            for s in ["ok", "skipped", "failed"]
                        ):
                            status = after_part.split()[0]
                            if status == "ok":
                                passed_tests.add(current_test)
                            elif status == "skipped":
                                skipped_tests.add(current_test)
                            elif status == "failed":
                                failed_tests.add(current_test)
                            current_test = None
            # Check for status in subsequent lines (case-insensitive, handles messages)
            elif current_test:
                lower_line = line_strip.lower()
                # Match exact status or status with trailing messages
                if any(lower_line.startswith(s) for s in ["ok", "skipped", "failed"]):
                    status = lower_line.split()[0]
                    if status == "ok":
                        passed_tests.add(current_test)
                    elif status == "skipped":
                        skipped_tests.add(current_test)
                    elif status == "failed":
                        failed_tests.add(current_test)
                    current_test = None
        # Parse Meson-style tests (captures full test description)
        meson_pattern = re.compile(
            r"\[\s*(SUCCESS|SKIPPED|FAILED)\s*\]\s+(.*)", re.IGNORECASE
        )
        for match in meson_pattern.finditer(log):
            status = match.group(1).upper()
            test_name = match.group(2).strip()
            if status == "SUCCESS":
                passed_tests.add(test_name)
            elif status == "SKIPPED":
                skipped_tests.add(test_name)
            elif status == "FAILED":
                failed_tests.add(test_name)
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
