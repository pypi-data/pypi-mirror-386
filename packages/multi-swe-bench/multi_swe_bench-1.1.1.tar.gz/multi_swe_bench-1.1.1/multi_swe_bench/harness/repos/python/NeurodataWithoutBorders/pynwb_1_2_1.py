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
pip install -r requirements.txt -r requirements-dev.txt -r requirements-doc.txt
###ACTION_DELIMITER###
echo 'python test.py -v' > /home/pynwb/test_commands.sh && chmod +x /home/pynwb/test_commands.sh
###ACTION_DELIMITER###
bash /home/pynwb/test_commands.sh
###ACTION_DELIMITER###
python setup.py develop
###ACTION_DELIMITER###
pip install pandas
###ACTION_DELIMITER###

###ACTION_DELIMITER###
pip install h5py hdmf
###ACTION_DELIMITER###
pip uninstall -y hdmf && pip install 'hdmf>=1.5.4,<2'
###ACTION_DELIMITER###
python setup.py develop
###ACTION_DELIMITER###
bash /home/pynwb/test_commands.sh
###ACTION_DELIMITER###
pip uninstall -y ruamel.yaml && pip install 'ruamel.yaml<0.18'
###ACTION_DELIMITER###
bash /home/pynwb/test_commands.sh
###ACTION_DELIMITER###
git submodule update --init --recursive
###ACTION_DELIMITER###
bash /home/pynwb/test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
python test.py -v

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
python test.py -v

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
python test.py -v

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
RUN git clone https://github.com/NeurodataWithoutBorders/pynwb.git /home/pynwb

WORKDIR /home/pynwb
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("NeurodataWithoutBorders", "pynwb_1_2_1")
class PYNWB_1_2_1(Instance):
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
        # Regex to match test result lines
        test_line_pattern = re.compile(
            r"^\s*\|\s*([^|]+?)\s*\|.*\|\s*(pass|fail|error)\s*(\|)?\s*$"
        )
        ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
        # Track the last status for each test
        test_status = {}
        for line in log.splitlines():
            clean_line = ansi_escape.sub("", line)
            match = test_line_pattern.match(clean_line)
            if match:
                raw_name = match.group(1).strip()
                # Normalize test name: remove trailing colons and excessive whitespace
                test_name = re.sub(r":\s*$", "", raw_name)
                status = match.group(2)
                # Always update to the latest status
                test_status[test_name] = status
        passed_tests = {
            name for name, status in test_status.items() if status == "pass"
        }
        failed_tests = {
            name for name, status in test_status.items() if status in ("fail", "error")
        }
        skipped_tests = set()  # Not present in your logs
        # Remove any overlap: a test can only be in one set, and the last status wins
        failed_tests -= passed_tests

        return TestResult(
            passed_count=len(passed_tests),
            failed_count=len(failed_tests),
            skipped_count=len(skipped_tests),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
        )
