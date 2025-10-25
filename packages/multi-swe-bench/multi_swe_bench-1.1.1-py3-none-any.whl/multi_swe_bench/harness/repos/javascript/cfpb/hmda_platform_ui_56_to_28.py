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
        return "node:18-bookworm"

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
                """sed -i '$ a deb [trusted=yes] http://archive.debian.org/debian buster main' /etc/apt/sources.list
###ACTION_DELIMITER###
ls -l /etc/apt/
###ACTION_DELIMITER###
echo 'deb [trusted=yes] http://archive.debian.org/debian buster main' > /etc/apt/sources.list.d/buster.list
###ACTION_DELIMITER###
apt-get update
###ACTION_DELIMITER###
apt-get install -y python2.7
###ACTION_DELIMITER###
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
###ACTION_DELIMITER###
export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
###ACTION_DELIMITER###
nvm install 6
###ACTION_DELIMITER###
npm install
###ACTION_DELIMITER###
rm -rf node_modules && npm cache clean --force && npm install
###ACTION_DELIMITER###
rm -rf node_modules package-lock.json ~/.npm && npm cache clean --force && npm install
###ACTION_DELIMITER###
rm -rf node_modules package-lock.json ~/.npm && npm cache clean --force && npm install --no-optional
###ACTION_DELIMITER###
npm install -g npm@6 && rm -rf node_modules package-lock.json ~/.npm && npm cache clean --force && npm install
###ACTION_DELIMITER###
npm install -g yarn@1.22.19 && yarn install
###ACTION_DELIMITER###
nvm reinstall 6
###ACTION_DELIMITER###
nvm install 6 --force
###ACTION_DELIMITER###
rm -rf node_modules package-lock.json && npm cache clean --force && npm install
###ACTION_DELIMITER###
nvm reinstall 6 && rm -rf node_modules package-lock.json && npm cache clean --force && npm install
###ACTION_DELIMITER###
nvm install 6 --force && rm -rf node_modules package-lock.json && npm cache clean --force && npm install
###ACTION_DELIMITER###
nvm reinstall 6 && rm -rf node_modules package-lock.json && npm cache clean --force && npm install
###ACTION_DELIMITER###
nvm install 6 --force && rm -rf node_modules package-lock.json && npm cache clean --force && npm install
###ACTION_DELIMITER###
nvm install 6.17.1 --reinstall-packages-from=6.17.1 && rm -rf node_modules package-lock.json && npm cache clean --force && npm install
###ACTION_DELIMITER###
rm -rf /usr/local/lib/node_modules/npm && nvm install 6 --force && rm -rf node_modules package-lock.json && npm cache clean --force && npm install
###ACTION_DELIMITER###
nvm uninstall 6 && nvm install 6 && npm --version
###ACTION_DELIMITER###
nvm install 10 && nvm use 10 && nvm uninstall 6 && nvm install 6 && npm --version
###ACTION_DELIMITER###
rm -rf node_modules package-lock.json && npm cache clean --force && npm install
###ACTION_DELIMITER###
npm install -g yarn@1.22.19 && yarn install
###ACTION_DELIMITER###
yarn install --ignore-engines
###ACTION_DELIMITER###
npm test -- --verbose
###ACTION_DELIMITER###
echo 'npm test -- --verbose' > test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
npm test -- --verbose

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
npm test -- --verbose

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
npm test -- --verbose

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
FROM node:18-bookworm

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
RUN git clone https://github.com/cfpb/hmda-platform-ui.git /home/hmda-platform-ui

WORKDIR /home/hmda-platform-ui
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("cfpb", "hmda_platform_ui_56_to_28")
class HMDA_PLATFORM_UI_56_TO_28(Instance):
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

        lines = log.split("\n")
        current_suite = None
        for i, line in enumerate(lines):
            # Check if the line is a test file result (PASS/FAIL)
            if re.match(r"^(PASS|FAIL)\s+__tests__\/.*\.js", line.strip()):
                # Next line is the suite name
                if i + 1 < len(lines):
                    current_suite = lines[i + 1].strip()
            # Check if the line is a test case with ✓ or ✕
            elif re.match(r"^\s{2}(✓|✕)\s+", line):
                if current_suite:
                    match = re.match(r"^\s{2}(✓|✕)\s+(.*)$", line)
                    if match:
                        status = match.group(1)
                        desc = match.group(2)
                        test_name = f"{current_suite} {desc}"
                        if status == "✓":
                            passed_tests.add(test_name)
                        elif status == "✕":
                            failed_tests.add(test_name)
            # Check for skipped tests (example pattern)
            elif re.match(r"^\s{2}- SKIPPED\s+", line):
                if current_suite:
                    match = re.match(r"^\s{2}- SKIPPED\s+(.*)$", line)
                    if match:
                        desc = match.group(1)
                        test_name = f"{current_suite} {desc}"
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
