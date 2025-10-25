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
        return "python:3.8-slim"

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
ls -al tests
###ACTION_DELIMITER###
which pip2 || which pip
###ACTION_DELIMITER###
pip --version
###ACTION_DELIMITER###
which pip2
###ACTION_DELIMITER###
apt-get update && apt-get install -y python2-pip
###ACTION_DELIMITER###
curl -O https://bootstrap.pypa.io/pip/2.7/get-pip.py && python2.7 get-pip.py
###ACTION_DELIMITER###
apt-get update && apt-get install -y curl
###ACTION_DELIMITER###
curl -O https://bootstrap.pypa.io/pip/2.7/get-pip.py && python2.7 get-pip.py
###ACTION_DELIMITER###
which python2
###ACTION_DELIMITER###
apt-get update && apt-get install -y python2.7
###ACTION_DELIMITER###
apt-get install -y python2
###ACTION_DELIMITER###
pip install nose astor flake8 Sphinx coverage
###ACTION_DELIMITER###
pip install -e .
###ACTION_DELIMITER###

###ACTION_DELIMITER###
lsb_release -a || cat /etc/os-release
###ACTION_DELIMITER###

###ACTION_DELIMITER###
apt-get install -y wget build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev
###ACTION_DELIMITER###
wget https://www.python.org/ftp/python/2.7.18/Python-2.7.18.tgz && tar xzf Python-2.7.18.tgz
###ACTION_DELIMITER###
cd Python-2.7.18 && ./configure --prefix=/usr/local/python2.7
###ACTION_DELIMITER###
make -j 2 && make install
###ACTION_DELIMITER###
/usr/local/python2.7/bin/python2.7 --version
###ACTION_DELIMITER###
/usr/local/python2.7/bin/python2.7 /home/hy/get-pip.py
###ACTION_DELIMITER###
/usr/local/python2.7/bin/pip install -r /home/hy/requirements-dev.txt
###ACTION_DELIMITER###
/usr/local/python2.7/bin/pip install -e /home/hy
###ACTION_DELIMITER###
echo '/usr/local/python2.7/bin/nosetests -sv' > /home/hy/test_commands.sh && chmod +x /home/hy/test_commands.sh
###ACTION_DELIMITER###
cd /home/hy && bash test_commands.sh
###ACTION_DELIMITER###
""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
/usr/local/python2.7/bin/nosetests -sv

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
/usr/local/python2.7/bin/nosetests -sv

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
/usr/local/python2.7/bin/nosetests -sv

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
FROM python:3.8-slim

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
RUN git clone https://github.com/hylang/hy.git /home/hy

WORKDIR /home/hy
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("hylang", "hy_0_9_5")
class HY_0_9_5(Instance):
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
        # Regular expressions for test result lines
        pass_re = re.compile(r"^(.*) \.\.\. ok$", re.MULTILINE)
        fail_re = re.compile(r"^(.*) \.\.\. ERROR$", re.MULTILINE)
        skip_re = re.compile(r"^(.*) \.\.\. (SKIP|skipped)$", re.MULTILINE)
        for match in pass_re.finditer(log):
            test_name = match.group(1).strip()
            passed_tests.add(test_name)
        for match in fail_re.finditer(log):
            test_name = match.group(1).strip()
            failed_tests.add(test_name)
        for match in skip_re.finditer(log):
            test_name = match.group(1).strip()
            skipped_tests.add(test_name)

        return TestResult(
            passed_count=len(passed_tests),
            failed_count=len(failed_tests),
            skipped_count=len(skipped_tests),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
        )
