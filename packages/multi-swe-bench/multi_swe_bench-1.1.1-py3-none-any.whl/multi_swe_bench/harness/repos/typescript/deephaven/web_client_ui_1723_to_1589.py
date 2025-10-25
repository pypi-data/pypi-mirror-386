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
        return "node:20"

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
                """npm install
###ACTION_DELIMITER###
npx playwright install
###ACTION_DELIMITER###
echo -e '#!/bin/bash
set -e
npm test -- --verbose --watchAll=false --changedSince=""
npm run e2e -- --reporter=list' > test_commands.sh
###ACTION_DELIMITER###
chmod +x test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo -e '#!/bin/bash
set -e
jest --verbose --watchAll=false ./...
npm run e2e -- --reporter=list' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo -e '#!/bin/bash
set -e
npx jest --verbose --watchAll=false ./...
npm run e2e -- --reporter=list' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
npx playwright install-deps
###ACTION_DELIMITER###
bash test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
#!/bin/bash
set -e
npx jest --verbose --watchAll=false ./...
npm run e2e -- --reporter=list

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
#!/bin/bash
set -e
npx jest --verbose --watchAll=false ./...
npm run e2e -- --reporter=list

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
#!/bin/bash
set -e
npx jest --verbose --watchAll=false ./...
npm run e2e -- --reporter=list

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
FROM node:20

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
RUN git clone https://github.com/deephaven/web-client-ui.git /home/web-client-ui

WORKDIR /home/web-client-ui
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("deephaven", "web_client_ui_1723_to_1589")
class WEB_CLIENT_UI_1723_TO_1589(Instance):
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
        import json

        # Parse passed test suites (PASS followed by test name)
        pass_suite_pattern = re.compile(r"\[\d+\]\s+PASS\s+(.*?)\s*$", re.MULTILINE)
        passed_suites = pass_suite_pattern.findall(log)
        passed_tests.update(passed_suites)
        # Parse individual passed tests (✓ with optional leading spaces)
        pass_test_pattern = re.compile(r"\s*✓\s+(.*?)\s*\(\d+ ms\)", re.MULTILINE)
        passed_tests_list = pass_test_pattern.findall(log)
        passed_tests.update(passed_tests_list)
        # Parse failed test suites (FAIL followed by test name)
        fail_suite_pattern = re.compile(r"\[\d+\]\s+FAIL\s+(.*?)\s*$", re.MULTILINE)
        failed_suites = fail_suite_pattern.findall(log)
        failed_tests.update(failed_suites)
        # Parse individual failed tests from error context (test name in error messages)
        fail_test_pattern = re.compile(r"\s*✕\s+(.*?)\s*\(\d+ ms\)", re.MULTILINE)
        failed_tests_list = fail_test_pattern.findall(log)
        failed_tests.update(failed_tests_list)
        # Extract test names from error file paths if individual failures not captured
        error_path_pattern = re.compile(r"\((.*?/)?(.*?):\d+:\d+\)", re.MULTILINE)
        error_tests = [match[1] for match in error_path_pattern.findall(log)]
        failed_tests.update(error_tests)
        # Parse skipped tests from summary (e.g., '[11079]   75 skipped')
        skip_count_pattern = re.compile(r"\[\d+\]\s+(\d+)\s+skipped", re.MULTILINE)
        skip_count = skip_count_pattern.findall(log)
        if skip_count:
            skipped_tests.add(f"{skip_count[0]} tests skipped")
        # Parse individual skipped tests from entries (e.g., '[webkit] › ...')
        skip_test_pattern = re.compile(r"\[webkit\] › (.*)", re.MULTILINE)
        skipped_tests_list = skip_test_pattern.findall(log)
        skipped_tests.update(skipped_tests_list)
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
