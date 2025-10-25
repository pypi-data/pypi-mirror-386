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
                """apt-get update
###ACTION_DELIMITER###
apt-get install -y build-essential xvfb libqt5x11extras5 libxcb-xinerama0 libgl1-mesa-glx libglib2.0-0
###ACTION_DELIMITER###
./install.sh
###ACTION_DELIMITER###
apt-get install -y wget
###ACTION_DELIMITER###
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
###ACTION_DELIMITER###
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda
###ACTION_DELIMITER###
export PATH="$HOME/miniconda/bin:$PATH" && source $HOME/miniconda/etc/profile.d/conda.sh && conda init bash
###ACTION_DELIMITER###
source /root/.bashrc
###ACTION_DELIMITER###
./install.sh
###ACTION_DELIMITER###
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
###ACTION_DELIMITER###
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
###ACTION_DELIMITER###
./install.sh
###ACTION_DELIMITER###
conda activate mantidimaging
###ACTION_DELIMITER###
pip install -r deps/dev-requirements.pip
###ACTION_DELIMITER###
echo 'QT_QPA_PLATFORM=offscreen xvfb-run -s "-screen 0 1024x768x24" pytest -v --no-header -rA -p no:cacheprovider' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install SharedArray
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install --upgrade numpy
###ACTION_DELIMITER###
pip install --upgrade pillow
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install pyqtgraph
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install pyqt5
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install numpy==1.23.5
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install requests-futures
###ACTION_DELIMITER###
bash test_commands.sh
###ACTION_DELIMITER###
pip install python-socketio
###ACTION_DELIMITER###
pip install eventlet
###ACTION_DELIMITER###

###ACTION_DELIMITER###
pip install websocket-client
###ACTION_DELIMITER###
echo 'conda run -n mantidimaging xvfb-run -s "-screen 0 1024x768x24" pytest -v --no-header -rA -p no:cacheprovider' > test_commands.sh
###ACTION_DELIMITER###
echo 'conda run -n mantidimaging QT_QPA_PLATFORM=offscreen xvfb-run -s "-screen 0 1024x768x24" pytest -v --no-header -rA -p no:cacheprovider' > test_commands.sh
###ACTION_DELIMITER###
bash test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
conda run -n mantidimaging QT_QPA_PLATFORM=offscreen xvfb-run -s "-screen 0 1024x768x24" pytest -v --no-header -rA -p no:cacheprovider

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
conda run -n mantidimaging QT_QPA_PLATFORM=offscreen xvfb-run -s "-screen 0 1024x768x24" pytest -v --no-header -rA -p no:cacheprovider

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
conda run -n mantidimaging QT_QPA_PLATFORM=offscreen xvfb-run -s "-screen 0 1024x768x24" pytest -v --no-header -rA -p no:cacheprovider

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
RUN git clone https://github.com/mantidproject/mantidimaging.git /home/mantidimaging

WORKDIR /home/mantidimaging
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("mantidproject", "mantidimaging_523_to_506")
class MANTIDIMAGING_523_TO_506(Instance):
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

        # Regex pattern to match test lines with status
        pattern = r"^(?:(mantidimaging/.+?\.py::.+?)\s+(PASSED|FAILED|SKIPPED)\s+\[\s*\d+%?\])|(?:(PASSED|FAILED|SKIPPED)\s+\[\d+\]\s+(mantidimaging/.+?\.py::.+?))|(?:(PASSED|FAILED|SKIPPED)\s+(mantidimaging/.+?\.py::.+?))$"
        matches = re.finditer(pattern, log, re.MULTILINE)
        for match in matches:
            test_name = None
            status = None
            if match.group(1) and match.group(2):
                test_name = match.group(1).strip()
                status = match.group(2)
            elif match.group(3) and match.group(4):
                test_name = match.group(4).strip()
                status = match.group(3)
            if test_name and status:
                if status == "PASSED":
                    passed_tests.add(test_name)
                elif status == "FAILED":
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
