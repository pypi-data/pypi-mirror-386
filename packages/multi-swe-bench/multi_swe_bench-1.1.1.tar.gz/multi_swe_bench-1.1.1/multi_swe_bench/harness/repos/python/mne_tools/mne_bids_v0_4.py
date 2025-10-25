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

    def dependency(self) -> str:
        return "python:3.9-slim"

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
pip install -r requirements.txt
###ACTION_DELIMITER###
python setup.py develop
###ACTION_DELIMITER###
echo "pytest --no-header -rA --tb=no -p no:cacheprovider mne_bids" > test_commands.sh
###ACTION_DELIMITER###
bash /home/mne-bids/test_commands.sh
###ACTION_DELIMITER###
pip install pytest-cov==2.8.1
###ACTION_DELIMITER###
bash /home/mne-bids/test_commands.sh
###ACTION_DELIMITER###
echo "pytest -rA --tb=no -p no:cacheprovider mne_bids" > test_commands.sh
###ACTION_DELIMITER###
bash /home/mne-bids/test_commands.sh
###ACTION_DELIMITER###
echo "pytest -v -rA --tb=no -p no:cacheprovider mne_bids" > test_commands.sh
###ACTION_DELIMITER###
bash /home/mne-bids/test_commands.sh
###ACTION_DELIMITER###
echo "pytest -v -rA -p no:cacheprovider mne_bids" > test_commands.sh
###ACTION_DELIMITER###
bash /home/mne-bids/test_commands.sh
###ACTION_DELIMITER###
pip install mne==0.21.2
###ACTION_DELIMITER###
bash /home/mne-bids/test_commands.sh
###ACTION_DELIMITER###
pip install numpy==1.26.4
###ACTION_DELIMITER###
bash /home/mne-bids/test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
pytest -v -rA -p no:cacheprovider mne_bids

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
pytest -v -rA -p no:cacheprovider mne_bids

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
pytest -v -rA -p no:cacheprovider mne_bids

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
FROM python:3.9-slim

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
RUN git clone https://github.com/mne-tools/mne-bids.git /home/mne-bids

WORKDIR /home/mne-bids
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("mne-tools", "mne-bids_v0_4")
class MNE_BIDS_V0_4(Instance):
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
        # Regular expression to match test result lines
        # Example: mne_bids/tests/test_path.py::test_print_dir_tree PASSED [ 22%]
        test_line_re = re.compile(
            r"^(.*?)::([\w\[\]\-]+)(?:\[.*?\])?\s+(PASSED|FAILED|ERROR|SKIPPED)"
        )
        for line in log.splitlines():
            match = test_line_re.match(line)
            if match:
                test_path = match.group(1).strip()
                test_name = match.group(2).strip()
                status = match.group(3)
                full_test_name = f"{test_path}::{test_name}"
                if status == "PASSED":
                    passed_tests.add(full_test_name)
                elif status == "FAILED" or status == "ERROR":
                    failed_tests.add(full_test_name)
                elif status == "SKIPPED":
                    skipped_tests.add(full_test_name)

        return TestResult(
            passed_count=len(passed_tests),
            failed_count=len(failed_tests),
            skipped_count=len(skipped_tests),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
        )
