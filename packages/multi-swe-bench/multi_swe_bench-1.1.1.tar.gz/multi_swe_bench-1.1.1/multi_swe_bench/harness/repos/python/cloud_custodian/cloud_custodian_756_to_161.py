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
                """ls
###ACTION_DELIMITER###
cat requirements-dev.txt
###ACTION_DELIMITER###
pip install -r requirements-dev.txt
###ACTION_DELIMITER###
cat Makefile
###ACTION_DELIMITER###
echo 'AWS_ACCESS_KEY_ID=foo AWS_SECRET_ACCESS_KEY=bar AWS_DEFAULT_REGION=us-east-1 nosetests -v --processes=-1 tests' > test_commands.sh
###ACTION_DELIMITER###
cat test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
ls tests
###ACTION_DELIMITER###
make develop
###ACTION_DELIMITER###
apt-get update && apt-get install -y make
###ACTION_DELIMITER###
make develop
###ACTION_DELIMITER###
pip install virtualenv
###ACTION_DELIMITER###
apt-get update && apt-get install -y python2.7
###ACTION_DELIMITER###
echo 'deb http://deb.debian.org/debian bullseye main' >> /etc/apt/sources.list && apt-get update && apt-get install -y python2.7
###ACTION_DELIMITER###
make develop
###ACTION_DELIMITER###
curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py && python2.7 get-pip.py && pip2 install virtualenv
###ACTION_DELIMITER###
apt-get update && apt-get install -y curl
###ACTION_DELIMITER###
curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py && python2.7 get-pip.py && pip2 install virtualenv
###ACTION_DELIMITER###
make develop
###ACTION_DELIMITER###
virtualenv --python=/usr/bin/python2.7 .
###ACTION_DELIMITER###
source bin/activate && pip install -r requirements-dev.txt && python setup.py develop
###ACTION_DELIMITER###
source bin/activate && pip install skew==0.18.0
###ACTION_DELIMITER###
source bin/activate && pip install skew==0.17.0
###ACTION_DELIMITER###
source bin/activate && pip install -r requirements-dev.txt && python setup.py develop
###ACTION_DELIMITER###
echo 'AWS_ACCESS_KEY_ID=foo AWS_SECRET_ACCESS_KEY=bar AWS_DEFAULT_REGION=us-east-1 ./bin/nosetests -v --processes=-1 tests' > test_commands.sh
###ACTION_DELIMITER###
cat test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
source bin/activate && pip install boto3==1.14.0 botocore==1.17.0
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
source bin/activate && pip install placebo==0.9.0
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo 'source bin/activate && AWS_ACCESS_KEY_ID=foo AWS_SECRET_ACCESS_KEY=bar AWS_DEFAULT_REGION=us-east-1 nosetests -v --processes=-1 tests' > test_commands.sh
###ACTION_DELIMITER###
cat test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo 'source bin/activate && AWS_ACCESS_KEY_ID=foo AWS_SECRET_ACCESS_KEY=bar AWS_DEFAULT_REGION=us-east-1 nosetests -v tests' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
echo 'source bin/activate && export PYTHONIOENCODING=utf-8 && AWS_ACCESS_KEY_ID=foo AWS_SECRET_ACCESS_KEY=bar AWS_DEFAULT_REGION=us-east-1 nosetests -v tests' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
source bin/activate && export PYTHONIOENCODING=utf-8 && AWS_ACCESS_KEY_ID=foo AWS_SECRET_ACCESS_KEY=bar AWS_DEFAULT_REGION=us-east-1 nosetests -v tests

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
source bin/activate && export PYTHONIOENCODING=utf-8 && AWS_ACCESS_KEY_ID=foo AWS_SECRET_ACCESS_KEY=bar AWS_DEFAULT_REGION=us-east-1 nosetests -v tests

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
source bin/activate && export PYTHONIOENCODING=utf-8 && AWS_ACCESS_KEY_ID=foo AWS_SECRET_ACCESS_KEY=bar AWS_DEFAULT_REGION=us-east-1 nosetests -v tests

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
RUN git clone https://github.com/cloud-custodian/cloud-custodian.git /home/cloud-custodian

WORKDIR /home/cloud-custodian
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("cloud-custodian", "cloud_custodian_756_to_161")
class CLOUD_CUSTODIAN_756_TO_161(Instance):
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
        passed_tests = set()
        failed_tests = set()
        skipped_tests = set()
        import re

        # Regex pattern to match test lines (e.g., [   1] test_name (class) ... status)
        passed_pattern = r"^(\w+)\s*\(.*?\)\s+\.\.\.\s+ok$"
        failed_pattern = r"^(ERROR|FAIL):\s*(\w+)\s*\(.*?\)"
        passed_matches = re.findall(passed_pattern, log, re.MULTILINE)
        failed_matches = re.findall(failed_pattern, log, re.MULTILINE)
        for test_name in passed_matches:
            passed_tests.add(test_name.strip())
        for status, test_name in failed_matches:
            failed_tests.add(test_name.strip())
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
