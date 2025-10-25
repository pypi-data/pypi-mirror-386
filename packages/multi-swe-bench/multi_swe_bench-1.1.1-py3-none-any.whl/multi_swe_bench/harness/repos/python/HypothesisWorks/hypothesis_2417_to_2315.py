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
ls -la hypothesis-python
###ACTION_DELIMITER###
apt-get update
###ACTION_DELIMITER###
apt-get install -y build-essential python3-dev
###ACTION_DELIMITER###
PIPELINE_WORKSPACE=1 ./build.sh test
###ACTION_DELIMITER###
pip install --upgrade pip setuptools wheel
###ACTION_DELIMITER###
PIPELINE_WORKSPACE=1 ./build.sh test
###ACTION_DELIMITER###
pip install numpy
###ACTION_DELIMITER###
PIPELINE_WORKSPACE=1 ./build.sh test
###ACTION_DELIMITER###
sed -i 's/numpy==1.18.4/numpy==1.23.5/' requirements/tools.txt
###ACTION_DELIMITER###
PIPELINE_WORKSPACE=1 ./build.sh test
###ACTION_DELIMITER###
sed -i 's/cffi==1.14.0/cffi==1.15.1/' requirements/tools.txt
###ACTION_DELIMITER###
PIPELINE_WORKSPACE=1 ./build.sh test
###ACTION_DELIMITER###
sed -i '/typed-ast/d' requirements/tools.txt
###ACTION_DELIMITER###
PIPELINE_WORKSPACE=1 ./build.sh test
###ACTION_DELIMITER###
sed -i 's/black==19.10b0/black==22.12.0/' requirements/tools.txt
###ACTION_DELIMITER###
PIPELINE_WORKSPACE=1 ./build.sh test
###ACTION_DELIMITER###
sed -i 's/click==7.1.2/click==8.1.3/' requirements/tools.txt
###ACTION_DELIMITER###
PIPELINE_WORKSPACE=1 ./build.sh test
###ACTION_DELIMITER###
sed -i 's/pathspec==0.8.0/pathspec==0.9.0/' requirements/tools.txt
###ACTION_DELIMITER###
PIPELINE_WORKSPACE=1 ./build.sh test
###ACTION_DELIMITER###
sed -i 's/typed-ast==.*/typed-ast==1.5.4/' requirements/tools.txt
###ACTION_DELIMITER###
sed -i '/typed-ast/d' requirements/tools.txt
###ACTION_DELIMITER###
sed -i 's/mypy==0.770/mypy==0.990/' requirements/tools.txt
###ACTION_DELIMITER###
sed -i 's/tox==3.15.1/tox==3.28.0/' requirements/tools.txt
###ACTION_DELIMITER###
echo 'typed-ast==1.5.4' >> requirements/tools.txt
###ACTION_DELIMITER###
PIPELINE_WORKSPACE=1 ./build.sh test
###ACTION_DELIMITER###
sed -i 's/typing-extensions==3.7.4.2/typing-extensions==4.0.0/' requirements/tools.txt
###ACTION_DELIMITER###
PIPELINE_WORKSPACE=1 ./build.sh test
###ACTION_DELIMITER###
echo 'pytest -v hypothesis-python/tests' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install pytest
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install -e hypothesis-python
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install pexpect python-dateutil pytz dpcontracts lark-parser pandas
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install numpy==1.21.6
###ACTION_DELIMITER###
pip install numpy==1.22.0
###ACTION_DELIMITER###
pip install pandas==1.5.3
###ACTION_DELIMITER###
pip install numpy==1.22.0 pandas==1.5.3
###ACTION_DELIMITER###
pip install numpy==1.23.2 pandas==1.5.3
###ACTION_DELIMITER###
bash test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
pytest -v hypothesis-python/tests

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
pytest -v hypothesis-python/tests

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
pytest -v hypothesis-python/tests

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
RUN git clone https://github.com/HypothesisWorks/hypothesis.git /home/hypothesis

WORKDIR /home/hypothesis
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("HypothesisWorks", "hypothesis_2417_to_2315")
class HYPOTHESIS_2417_TO_2315(Instance):
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
        import json

        # Extract test names and statuses using regex
        # Parse passed tests (format: <test_name> PASSED)
        passed_matches = re.findall(
            r"((?:hypothesis-python/)?tests/[\w/]+/test_\w+\.py::test_[\w\-\[\]]+) PASSED",
            log,
        )
        passed_tests.update(passed_matches)
        # Parse failed tests (format: FAILED <test_name>)
        failed_matches = re.findall(
            r"FAILED ((?:hypothesis-python/)?tests/[\w/]+/test_\w+\.py::test_[\w\-\[\]]+)",
            log,
        )
        failed_tests.update(failed_matches)
        # Parse skipped tests (format: SKIPPED <test_name> or <test_name> SKIPPED)
        skipped_matches = re.findall(
            r"SKIPPED ((?:hypothesis-python/)?tests/[\w/]+/test_\w+\.py::[\w:]+::test_[\w\-\[\]]+)",
            log,
        ) + re.findall(
            r"((?:hypothesis-python/)?tests/[\w/]+/test_\w+\.py::[\w:]+::test_[\w\-\[\]]+) SKIPPED",
            log,
        )
        skipped_tests.update(skipped_matches)
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
