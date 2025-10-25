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
        return "python:3.6-slim"

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
INSTALL_TEST_REQUIREMENTS="true" ./scripts/install_requirements.sh
###ACTION_DELIMITER###
apt-get update && apt-get install -y build-essential python3-dev
###ACTION_DELIMITER###
INSTALL_TEST_REQUIREMENTS="true" ./scripts/install_requirements.sh
###ACTION_DELIMITER###
sed -i 's/git:\/\/github.com/https:\/\/github.com/g' requirements_test.txt
###ACTION_DELIMITER###
INSTALL_TEST_REQUIREMENTS="true" ./scripts/install_requirements.sh
###ACTION_DELIMITER###
pytest -v
###ACTION_DELIMITER###
pip install torch==1.10.0+cpu -f https://download.pytorch.org/whl/cpu/stable.html
###ACTION_DELIMITER###
pip install torch==1.10.0
###ACTION_DELIMITER###
python -c 'import torch; print("PyTorch version:", torch.__version__)'
###ACTION_DELIMITER###
pytest -v
###ACTION_DELIMITER###
cat requirements.txt
###ACTION_DELIMITER###
pip uninstall -y torch && pip install torch==1.0.1
###ACTION_DELIMITER###
pip uninstall -y torch && pip install torch==1.4.0
###ACTION_DELIMITER###
pip uninstall -y spacy && pip install spacy==2.1.0 && python -m spacy download en
###ACTION_DELIMITER###
pip uninstall -y torch && pip install torch==1.0.1
###ACTION_DELIMITER###
pip uninstall -y torch && pip install torch==0.4.1
###ACTION_DELIMITER###
pip uninstall -y torch && pip install torch==1.0.0
###ACTION_DELIMITER###
pytest -v
###ACTION_DELIMITER###
pip install -e .
###ACTION_DELIMITER###
pip uninstall -y spacy thinc && pip install spacy==2.0.18 thinc==6.12.1 && pip install -e .
###ACTION_DELIMITER###
pip uninstall -y torch spacy thinc numpy nltk && pip install torch==0.4.1 spacy==2.0.18 thinc==6.12.1 numpy==1.15.4 nltk==3.2.5 && pip install -e .
###ACTION_DELIMITER###
pip install torch==1.0.0 spacy==2.0.18 thinc==6.12.1 numpy==1.15.4 nltk==3.2.5 && python -m spacy download en_core_web_sm==2.0.0 && pip install -e . --no-deps
###ACTION_DELIMITER###
pip uninstall -y en-core-web-sm && python -m spacy download en==2.0.0 && pytest -v
###ACTION_DELIMITER###
python -m spacy download en_core_web_sm==2.0.0 && pip install -e . && pytest -v
###ACTION_DELIMITER###
wget https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.0.0/en_core_web_sm-2.0.0.tar.gz && pip install en_core_web_sm-2.0.0.tar.gz && pip install -e . --no-deps && pytest -v
###ACTION_DELIMITER###
apt-get update && apt-get install -y wget && wget https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.0.0/en_core_web_sm-2.0.0.tar.gz && pip install en_core_web_sm-2.0.0.tar.gz && pip install -e . --no-deps && pytest -v
###ACTION_DELIMITER###
pip install https://download.pytorch.org/whl/cpu/torch-0.4.1-cp36-cp36m-linux_x86_64.whl && pip install -e . --no-deps && pytest -v
###ACTION_DELIMITER###
pip install torch==0.4.1+cpu -f https://download.pytorch.org/whl/cpu/stable && pip install spacy==2.0.18 && python -m spacy download en_core_web_sm==2.0.0 && pip install -e . --no-deps && pytest -v
###ACTION_DELIMITER###
pip install https://download.pytorch.org/whl/cpu/torch-0.4.1-cp36-cp36m-linux_x86_64.whl && pip install spacy==2.0.18 && wget https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.0.0/en_core_web_sm-2.0.0.tar.gz && pip install en_core_web_sm-2.0.0.tar.gz && pip install -e . --no-deps && pytest -v
###ACTION_DELIMITER###
pip install torch==0.4.1 spacy==2.0.18 numpy==1.15.4 nltk==3.2.5 thinc==6.12.1 && python -m spacy download en_core_web_sm==2.0.0 && pip install -e . && pytest -v
###ACTION_DELIMITER###
wget https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.0.0/en_core_web_sm-2.0.0.tar.gz && pip install en_core_web_sm-2.0.0.tar.gz && pip install -e . --no-deps && pytest -v
###ACTION_DELIMITER###
pip uninstall -y overrides && pip install overrides==1.9.0 && pytest -v
###ACTION_DELIMITER###
echo 'pytest -v' > /home/allennlp/test_commands.sh && chmod +x /home/allennlp/test_commands.sh""",
            ),
            File(
                ".",
                "run.sh",
                """#!/bin/bash
cd /home/[[REPO_NAME]]
pytest -v

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
pytest -v

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
pytest -v

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

# Choose an appropriate base image based on the project's requirements - replace python:3.6-slim with actual base image
# For example: FROM ubuntu:**, FROM python:**, FROM node:**, FROM centos:**, etc.
FROM python:3.6-slim

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
RUN git clone https://github.com/allenai/allennlp.git /home/allennlp

WORKDIR /home/allennlp
RUN git reset --hard
RUN git checkout {pr.base.sha}
"""
        dockerfile_content += f"""
{copy_commands}
"""
        return dockerfile_content.format(pr=self.pr)


@Instance.register("allenai", "allennlp_318_to_257")
class ALLENNLP_318_TO_257(Instance):
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

        # Regex pattern to match test lines with status
        test_pattern = re.compile(
            r"^(tests/.*?) (PASSED|FAILED|SKIPPED)\s+\[\s*\d+%\]|"  # Format 1: test ... STATUS [x%]
            r"^(PASSED|FAILED|SKIPPED)\s+(tests/.*?)(?:\s+-.*)?$"  # Format 2: STATUS test ... (ignore - ...)
        )
        for line in log.splitlines():
            line = line.strip()
            match = test_pattern.match(line)
            if match:
                # Determine which format matched
                if match.group(1):
                    test_name = match.group(1)
                    status = match.group(2)
                else:
                    test_name = match.group(4)
                    status = match.group(3)
                # Add to the appropriate set
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
