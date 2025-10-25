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
        return "python:3.10-slim"

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
ls -la tests
###ACTION_DELIMITER###
pip install --upgrade pip
###ACTION_DELIMITER###
pip install -r tests/requirements.txt
###ACTION_DELIMITER###
pip install -e .
###ACTION_DELIMITER###
python bootstrap.py
###ACTION_DELIMITER###
sed -i 's/collections.MutableMapping/collections.abc.MutableMapping/g' pkg_resources/_vendor/pyparsing.py
###ACTION_DELIMITER###
python bootstrap.py
###ACTION_DELIMITER###
sed -i 's/collections.Iterable/collections.abc.Iterable/g' pkg_resources/_vendor/pyparsing.py
###ACTION_DELIMITER###
python bootstrap.py
###ACTION_DELIMITER###
sed -i 's/getattr(html, \'unescape\', html_parser.HTMLParser().unescape)/html.unescape/g' setuptools/py33compat.py
###ACTION_DELIMITER###
sed -i "s/getattr(html, 'unescape', html_parser.HTMLParser().unescape)/html.unescape/g" setuptools/py33compat.py
###ACTION_DELIMITER###
sed -i 's/html_parser\.HTMLParser()\.unescape/html.unescape/g' setuptools/py33compat.py
###ACTION_DELIMITER###
python bootstrap.py
###ACTION_DELIMITER###
pip install -e .
###ACTION_DELIMITER###
python setup.py develop
###ACTION_DELIMITER###
echo 'pytest -v --cov-config=tox.ini --cov-report=term setuptools/' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
sed -i 's/collections.MutableMapping/collections.abc.MutableMapping/g' setuptools/_vendor/pyparsing.py
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
sed -i 's/collections.Iterable/collections.abc.Iterable/g' setuptools/_vendor/pyparsing.py
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
sed -i 's/_dummy_thread/_dummy_threading/g' setuptools/_vendor/six.py
###ACTION_DELIMITER###
sed -i 's/pytest -v/pytest -v --ignore setuptools\/command\/bdist_wininst.py/' test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
sed -i 's/_dummy_threading/dummy_threading/g' setuptools/_vendor/six.py
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
sed -i 's/--ignore setuptools\\/command\\/bdist_wininst.py/--ignore setuptools\\/command\\/bdist_wininst.py --ignore setuptools\\/_vendor\\//' test_commands.sh
###ACTION_DELIMITER###
sed -i 's|--ignore setuptools/command/bdist_wininst.py|--ignore setuptools/command/bdist_wininst.py --ignore setuptools/_vendor/|' test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
pytest -v --ignore setuptools/command/bdist_wininst.py --ignore setuptools/_vendor/ --cov-config=tox.ini --cov-report=term setuptools/

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
pytest -v --ignore setuptools/command/bdist_wininst.py --ignore setuptools/_vendor/ --cov-config=tox.ini --cov-report=term setuptools/

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
pytest -v --ignore setuptools/command/bdist_wininst.py --ignore setuptools/_vendor/ --cov-config=tox.ini --cov-report=term setuptools/

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
FROM python:3.10-slim

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
RUN git clone https://github.com/pypa/setuptools.git /home/setuptools

WORKDIR /home/setuptools
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("pypa", "setuptools_1365_to_1364")
class SETUPTOOLS_1365_TO_1364(Instance):
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

        # Pattern for individual test lines (PASSED, FAILED, SKIPPED, XPASS, XFAIL)
        test_line_pattern = re.compile(
            r"^(.+?)\s+(PASSED|FAILED|SKIPPED|XPASS|XFAIL)\s+.*$", re.MULTILINE
        )
        for match in test_line_pattern.finditer(log):
            test_name = match.group(1).strip()
            status = match.group(2)
            if status == "PASSED":
                passed_tests.add(test_name)
            elif status == "FAILED":
                failed_tests.add(test_name)
            elif status == "SKIPPED":
                skipped_tests.add(test_name)
            elif status == "XPASS":
                passed_tests.add(test_name)  # Unexpected pass, considered passed
            elif status == "XFAIL":
                failed_tests.add(test_name)  # Expected failure, considered failed
        # Pattern for summary lines (XFAIL, XPASS, SKIPPED)
        summary_pattern = re.compile(
            r"^(XFAIL|XPASS|SKIPPED)\s+(?:\[\d+\]\s+)?(.+?)\s+-?.*$", re.MULTILINE
        )
        for match in summary_pattern.finditer(log):
            status = match.group(1)
            test_name = match.group(2).strip()
            if status == "XPASS":
                passed_tests.add(test_name)
            elif status == "XFAIL":
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
