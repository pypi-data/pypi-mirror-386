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
                """echo fs.inotify.max_user_watches=524288 | tee -a /etc/sysctl.conf && sysctl -p
###ACTION_DELIMITER###
apt-get update && apt-get install -y python2.7
###ACTION_DELIMITER###
apt-get install -y build-essential
###ACTION_DELIMITER###
curl -fsSL https://deb.nodesource.com/setup_14.x | bash - && apt-get install -y nodejs
###ACTION_DELIMITER###
apt-get install -y curl
###ACTION_DELIMITER###
curl -fsSL https://deb.nodesource.com/setup_14.x | bash - && apt-get install -y nodejs
###ACTION_DELIMITER###
apt-get remove -y nodejs libnode72
###ACTION_DELIMITER###
curl -fsSL https://deb.nodesource.com/setup_14.x | bash - && apt-get install -y nodejs
###ACTION_DELIMITER###
npm install -g yarn && export PYTHON=python2.7 && yarn install
###ACTION_DELIMITER###
yarn cache clean && export PYTHON=python2.7 && yarn install
###ACTION_DELIMITER###
rm -rf /usr/local/share/.cache/yarn && rm -rf node_modules yarn.lock && export PYTHON=python2.7 && npm install --legacy-peer-deps
###ACTION_DELIMITER###
export PYTHON=python2.7 && npm install --legacy-peer-deps --ignore-scripts
###ACTION_DELIMITER###
echo 'yarn test --verbose --watchAll=false' > /home/politeiagui/test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
yarn test --verbose --watchAll=false

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
yarn test --verbose --watchAll=false

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
yarn test --verbose --watchAll=false

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
RUN git clone https://github.com/decred/politeiagui.git /home/politeiagui

WORKDIR /home/politeiagui
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("decred", "politeiagui_1299_to_1020")
class POLITEIAGUI_1299_TO_1020(Instance):
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
        passed_tests = set()
        failed_tests = set()
        skipped_tests = set()
        import re
        import sys

        # Extract passed tests (marked with ✓) - time suffix optional
        passed_pattern = re.compile(r"^\s+✓\s+(.*?)\s*(?:\(\d+ms\))?$", re.MULTILINE)
        passed_tests = set(test.strip() for test in passed_pattern.findall(log))
        # Extract failed tests (marked with ✕) - time suffix optional
        failed_pattern = re.compile(r"^\s+✕\s+(.*?)\s*(?:\(\d+ms\))?$", re.MULTILINE)
        failed_tests = set(test.strip() for test in failed_pattern.findall(log))
        # Extract summary counts for validation
        summary_pattern = re.compile(
            r"Tests:\s+(\d+)\s+failed,\s+(\d+)\s+passed", re.MULTILINE
        )
        summary_match = summary_pattern.search(log)
        if summary_match:
            expected_failed = int(summary_match.group(1))
            expected_passed = int(summary_match.group(2))
            # Validate parsed counts against summary
            if len(failed_tests) != expected_failed:
                print(
                    f"Warning: Parsed {len(failed_tests)} failed tests, but summary reports {expected_failed}",
                    file=sys.stderr,
                )
            if len(passed_tests) != expected_passed:
                print(
                    f"Warning: Parsed {len(passed_tests)} passed tests, but summary reports {expected_passed}",
                    file=sys.stderr,
                )
        else:
            expected_failed = 0
            expected_passed = 0
        # Extract skipped tests (marked with −)
        skipped_pattern = re.compile(
            r"^\s+−\s+([^\(]+?)\s*(?:\(\d+ms\))?$", re.MULTILINE
        )
        skipped_tests = set(skipped_pattern.findall(log))
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
