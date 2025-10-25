from typing import Dict, Set
import re

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
        return "node:14-bullseye"

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
                """ls -la
###ACTION_DELIMITER###
npm install -g yarn
###ACTION_DELIMITER###
yarn --version
###ACTION_DELIMITER###
yarn install
###ACTION_DELIMITER###
yarn test
###ACTION_DELIMITER###
echo 'yarn test' > test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
yarn test

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
yarn test

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
yarn test

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
FROM node:14-bullseye

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
RUN git clone https://github.com/angular-eslint/angular-eslint.git /home/angular-eslint

WORKDIR /home/angular-eslint
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("angular-eslint", "angular_eslint_313_to_70")
class ANGULAR_ESLINT_313_TO_70(Instance):
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
        passed_tests: Set[str] = set()  # Tests that passed successfully
        failed_tests: Set[str] = set()  # Tests that failed
        skipped_tests: Set[str] = set()  # Tests that were skipped
        # Split log into lines
        lines = log.split("\n")
        for line in lines:
            line = line.strip()
            # Capture passed tests (e.g., ": PASS tests/...")
            if ": PASS " in line:
                parts = line.split(": PASS ", 1)
                if len(parts) < 2:
                    continue
                test_part = parts[1]
                # Remove trailing time (e.g., " (6.451 s)")
                test_file = re.sub(r" \(\d+\.\d+ s\)$", "", test_part)
                # Extract rule name from test file path (e.g., "tests/rules/no-conflicting-lifecycle.test.ts" -> "no-conflicting-lifecycle")
                match = re.search(r"([^/]+)\.test\.ts$", test_file)
                if match:
                    rule_name = match.group(1)
                    passed_tests.add(rule_name)
                else:
                    # Fallback to full test file name if pattern doesn't match
                    passed_tests.add(test_file)
            # Capture failed tests (Jest uses "●" for failures)
            elif "●" in line:
                # Extract test name (e.g., "component-max-inline-declarations" from "● component-max-inline-declarations › ...")
                # Capture up to first '›' to get base test name
                match = re.search(r"●\s*([^›]+)", line)
                if match:
                    test_name = match.group(1).strip()
                    failed_tests.add(test_name)
            # Handle skipped tests
            elif ": SKIPPED " in line:
                parts = line.split(": SKIPPED ", 1)
                if len(parts) < 2:
                    continue
                test_part = parts[1]
                # Remove trailing time (e.g., " (6.451 s)")
                test_name = re.sub(r" \(\d+\.\d+ s\)$", "", test_part)
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
