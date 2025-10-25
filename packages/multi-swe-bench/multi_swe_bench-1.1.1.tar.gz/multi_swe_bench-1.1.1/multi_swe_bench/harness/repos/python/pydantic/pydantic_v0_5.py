import re
from typing import Optional

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

    def dependency(self) -> Image | None:
        return "python:3.7"

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
                """ls -al
###ACTION_DELIMITER###
pip install -U setuptools pip && pip install -r requirements.txt && pip install -U .
###ACTION_DELIMITER###
echo 'pytest --cov=pydantic
pip uninstall -y msgpack-python ujson
pytest --cov=pydantic' > /home/pydantic/test_commands.sh
###ACTION_DELIMITER###
chmod +x /home/pydantic/test_commands.sh && bash /home/pydantic/test_commands.sh
###ACTION_DELIMITER###
pip install --upgrade 'pytest>=6.0.0'
###ACTION_DELIMITER###
bash /home/pydantic/test_commands.sh
###ACTION_DELIMITER###
pip install --upgrade pytest-isort
###ACTION_DELIMITER###
bash /home/pydantic/test_commands.sh
###ACTION_DELIMITER###
pip install --upgrade pytest-sugar
###ACTION_DELIMITER###
bash /home/pydantic/test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
pytest --cov=pydantic
pip uninstall -y msgpack-python ujson
pytest --cov=pydantic

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
pytest --cov=pydantic
pip uninstall -y msgpack-python ujson
pytest --cov=pydantic

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
pytest --cov=pydantic
pip uninstall -y msgpack-python ujson
pytest --cov=pydantic

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
FROM python:3.7

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
RUN git clone https://github.com/pydantic/pydantic.git /home/pydantic

WORKDIR /home/pydantic
RUN git reset --hard
RUN git checkout 02dc2f2697602053ce83b45b015c464e0b6770bd

RUN git checkout {pr.base.sha}"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("pydantic", "pydantic_v0_5")
class PYDANTIC_V0_5(Instance):
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
        # Find the short test summary info section
        summary_match = re.search(r"=+ short test summary info =+[\s\S]+?=+", log)
        summary = summary_match.group(0) if summary_match else ""
        # Patterns for summary lines
        fail_pat = re.compile(r"FAILED ([^\s]+)")
        skip_pat = re.compile(r"SKIPPED ([^\s]+)")
        error_pat = re.compile(r"ERROR ([^\s]+)")
        for m in fail_pat.finditer(summary):
            failed_tests.add(m.group(1))
        for m in skip_pat.finditer(summary):
            skipped_tests.add(m.group(1))
        for m in error_pat.finditer(summary):
            failed_tests.add(m.group(1))
        # Parse progress lines for passed/skipped/failed tests
        progress_pat = re.compile(r"^(tests/[^\s]+\.py) ([.sF]+)", re.MULTILINE)
        for file_match in progress_pat.finditer(log):
            fname = file_match.group(1)
            status_str = file_match.group(2)
            # Find all test status chars
            for idx, ch in enumerate(status_str):
                # Try to get test function name from summary if available
                # Otherwise, use file name with index
                test_id = None
                if ch == ".":
                    # Passed test, but not listed in summary, so infer name
                    # Try to find matching test name in summary or fallback
                    test_id = f"{fname}::test_{idx + 1}"
                    passed_tests.add(test_id)
                elif ch == "s":
                    test_id = f"{fname}::test_{idx + 1}"
                    skipped_tests.add(test_id)
                elif ch == "F":
                    test_id = f"{fname}::test_{idx + 1}"
                    failed_tests.add(test_id)
        # Remove any overlap (e.g., if a test is both in failed and passed, keep failed)
        passed_tests -= failed_tests
        passed_tests -= skipped_tests
        skipped_tests -= failed_tests
        # If no summary and only error, try to extract error from summary
        if not summary and "ERROR" in log:
            for m in error_pat.finditer(log):
                failed_tests.add(m.group(1))

        return TestResult(
            passed_count=len(passed_tests),
            failed_count=len(failed_tests),
            skipped_count=len(skipped_tests),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
        )
