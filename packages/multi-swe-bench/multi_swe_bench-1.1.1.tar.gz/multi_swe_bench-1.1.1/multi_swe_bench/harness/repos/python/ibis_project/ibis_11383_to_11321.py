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
        return "ubuntu:latest"

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
ls ci
###ACTION_DELIMITER###
ls -a
###ACTION_DELIMITER###
ls .github
###ACTION_DELIMITER###
ls .github/workflows
###ACTION_DELIMITER###
echo 'uv run pytest -v --no-header -rA --tb=no -p no:cacheprovider --junitxml=junit.xml -m "core or benchmark" --numprocesses auto' > test_commands.sh
###ACTION_DELIMITER###
apt-get update && apt-get install -y curl
###ACTION_DELIMITER###
curl -LsSf https://astral.sh/uv/install.sh | sh
###ACTION_DELIMITER###
apt-get install -y just
###ACTION_DELIMITER###
just sync
###ACTION_DELIMITER###
export PATH="$HOME/.local/bin:$PATH"
###ACTION_DELIMITER###
just sync
###ACTION_DELIMITER###
apt-get install -y python3.9 python3.9-dev python3-pip
###ACTION_DELIMITER###
uv config set python.downloads allow
###ACTION_DELIMITER###
uv venv --python 3.9
###ACTION_DELIMITER###
export UV_PYTHON_DOWNLOADS=allow
###ACTION_DELIMITER###
uv venv --python 3.9
###ACTION_DELIMITER###
export UV_PYTHON_DOWNLOADS=true
###ACTION_DELIMITER###
uv venv --python 3.9
###ACTION_DELIMITER###
source .venv/bin/activate
###ACTION_DELIMITER###
just sync
###ACTION_DELIMITER###
apt-get install -y pkg-config libmysqlclient-dev
###ACTION_DELIMITER###
just sync
###ACTION_DELIMITER###
apt-get install -y libpq-dev
###ACTION_DELIMITER###
just sync
###ACTION_DELIMITER###
apt-get install -y build-essential
###ACTION_DELIMITER###
just sync
###ACTION_DELIMITER###
chmod +x test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
uv run pytest -v --no-header -rA --tb=no -p no:cacheprovider --junitxml=junit.xml -m "core or benchmark" --numprocesses auto

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
uv run pytest -v --no-header -rA --tb=no -p no:cacheprovider --junitxml=junit.xml -m "core or benchmark" --numprocesses auto

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
uv run pytest -v --no-header -rA --tb=no -p no:cacheprovider --junitxml=junit.xml -m "core or benchmark" --numprocesses auto

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

# Choose an appropriate base image based on the project's requirements - replace ubuntu:latest with actual base image
# For example: FROM ubuntu:**, FROM python:**, FROM node:**, FROM centos:**, etc.
FROM ubuntu:latest

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
RUN git clone https://github.com/ibis-project/ibis.git /home/ibis

WORKDIR /home/ibis
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("ibis-project", "ibis_11383_to_11321")
class IBIS_11383_TO_11321(Instance):
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

        # Regex pattern to match test status and name
        pattern = r"(PASSED|FAILED|SKIPPED|XFAIL|ERROR)\s+([\w\/]+\.py::[\w\[\]\-]+)"
        matches = re.findall(pattern, log)
        for status, test_name in matches:
            if status == "PASSED":
                passed_tests.add(test_name)
            elif status in ("FAILED", "XFAIL", "ERROR"):
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
