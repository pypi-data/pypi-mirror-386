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
        return "ubuntu:16.04"

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
cat requirements-dev.txt
###ACTION_DELIMITER###
python3 --version
###ACTION_DELIMITER###
apt-get update && apt-get install -y python3 python3-pip
###ACTION_DELIMITER###
python3 --version
###ACTION_DELIMITER###
apt-get install -y python3.6 python3.6-distutils
###ACTION_DELIMITER###
apt-get install -y software-properties-common && add-apt-repository ppa:deadsnakes/ppa && apt-get update
###ACTION_DELIMITER###
pip3 install --upgrade pip
###ACTION_DELIMITER###
pip3 install torch numpy
###ACTION_DELIMITER###
apt-get install -y curl git build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev
###ACTION_DELIMITER###
curl https://pyenv.run | bash
###ACTION_DELIMITER###
export PYENV_ROOT="$HOME/.pyenv" && export PATH="$PYENV_ROOT/bin:$PATH" && eval "$(pyenv init -)" && pyenv install 3.8.18
###ACTION_DELIMITER###
export PYENV_ROOT="$HOME/.pyenv" && export PATH="$PYENV_ROOT/bin:$PATH" && eval "$(pyenv init -)" && pyenv global 3.8.18 && python --version
###ACTION_DELIMITER###
python -m pip install --upgrade pip
###ACTION_DELIMITER###
python -m pip install torch numpy
###ACTION_DELIMITER###
python -m pip install -r requirements-dev.txt
###ACTION_DELIMITER###
python -m pip install -e .
###ACTION_DELIMITER###
echo 'pytest -v --device all --dtype float32,float64 --cov=kornia test/ --flake8 --mypy' > /home/kornia/test_commands.sh && chmod +x /home/kornia/test_commands.sh
###ACTION_DELIMITER###
bash /home/kornia/test_commands.sh
###ACTION_DELIMITER###
export PYENV_ROOT="$HOME/.pyenv" && export PATH="$PYENV_ROOT/bin:$PATH" && eval "$(pyenv init -)" && export PATH="$PYENV_ROOT/versions/3.8.18/bin:$PATH" && pytest -v --device all --dtype float32,float64 --cov=kornia test/ --flake8 --mypy""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/{pr.repo}
pytest -v --device all --dtype float32,float64 --cov=kornia test/ --flake8 --mypy

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
pytest -v --device all --dtype float32,float64 --cov=kornia test/ --flake8 --mypy

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
pytest -v --device all --dtype float32,float64 --cov=kornia test/ --flake8 --mypy

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
FROM ubuntu:16.04

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
RUN git clone https://github.com/kornia/kornia.git /home/kornia

WORKDIR /home/kornia
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("kornia", "kornia_v0_5_0")
class KORNIA_V0_5_0(Instance):
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
        # Regex pattern to match test result lines
        # Example: test/file.py::TestClass::test_name[param] PASSED [  0%]
        pattern = re.compile(r"^(.*?) (PASSED|FAILED|SKIPPED)\b", re.MULTILINE)
        for match in pattern.finditer(log):
            test_name, status = match.group(1), match.group(2)
            if status == "PASSED":
                passed_tests.add(test_name.strip())
            elif status == "FAILED":
                failed_tests.add(test_name.strip())
            elif status == "SKIPPED":
                skipped_tests.add(test_name.strip())

        return TestResult(
            passed_count=len(passed_tests),
            failed_count=len(failed_tests),
            skipped_count=len(skipped_tests),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
        )
