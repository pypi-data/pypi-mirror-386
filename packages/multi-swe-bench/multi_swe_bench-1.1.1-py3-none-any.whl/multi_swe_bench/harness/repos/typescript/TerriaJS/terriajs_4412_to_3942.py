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
        return "node:18"

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
                """apt-get update && apt-get install -y libgtk-3-0 libnotify4 libgconf-2-4 libnss3 libxss1 libasound2 xvfb libxtst6 libatspi2.0-0 libuuid1 libxcb1
###ACTION_DELIMITER###
echo 'deb [trusted=yes] http://archive.debian.org/debian buster main' > /etc/apt/sources.list.d/buster.list && echo 'deb [trusted=yes] http://archive.debian.org/debian-security buster/updates main' >> /etc/apt/sources.list.d/buster.list && apt-get update && apt-get install -y python2.7 && ln -s /usr/bin/python2.7 /usr/bin/python2
###ACTION_DELIMITER###
sed -i 's/git:\/\/github.com\/TerriaJS\//https:\/\/github.com\/TerriaJS\//g' package.json && curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash && source ~/.bashrc && nvm install 14 && nvm use 14 && npm install --legacy-peer-deps
###ACTION_DELIMITER###
echo 'xvfb-run -a npx gulp test-travis' > /home/terriajs/test_commands.sh
###ACTION_DELIMITER###
bash /home/terriajs/test_commands.sh
###ACTION_DELIMITER###
echo -e 'npx gulp build
xvfb-run -a npx gulp test-travis' > /home/terriajs/test_commands.sh
###ACTION_DELIMITER###
bash /home/terriajs/test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
npx gulp build
xvfb-run -a npx gulp test-travis

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
npx gulp build
xvfb-run -a npx gulp test-travis

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
npx gulp build
xvfb-run -a npx gulp test-travis

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

# Choose an appropriate base image based on the project's requirements - replace node:18 with actual base image
# For example: FROM ubuntu:**, FROM python:**, FROM node:**, FROM centos:**, etc.
FROM node:18

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
RUN git clone https://github.com/TerriaJS/terriajs.git /home/terriajs

WORKDIR /home/terriajs
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("TerriaJS", "terriajs_4412_to_3942")
class TERRIAJS_4412_TO_3942(Instance):
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
        passed_tests = set[str]  # Tests that passed successfully
        failed_tests = set[str]  # Tests that failed
        skipped_tests = set[str]  # Tests that were skipped
        import re

        # Extract all test names from the log
        test_pattern = re.compile(r"\./test/([\w/]+Spec)\.ts", re.IGNORECASE)
        all_tests = set(test_pattern.findall(log))
        # Extract failed tests (those with ERROR)
        failed_pattern = re.compile(r"ERROR in \./test/([\w/]+Spec)\.ts", re.IGNORECASE)
        failed_tests = set(failed_pattern.findall(log))
        # Passed tests are all tests not in failed_tests
        passed_tests = all_tests - failed_tests
        # Skipped tests are not identified in the current log patterns
        skipped_tests = set()
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
