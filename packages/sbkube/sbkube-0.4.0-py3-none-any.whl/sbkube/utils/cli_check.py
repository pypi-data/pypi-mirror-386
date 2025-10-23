import os
import shutil
import subprocess
import sys

from sbkube.exceptions import CliToolExecutionError, CliToolNotFoundError
from sbkube.utils.logger import logger


def check_helm_installed_or_exit():
    """helm 설치 확인 (테스트 가능한 버전)"""
    try:
        check_helm_installed()
    except (CliToolNotFoundError, CliToolExecutionError):
        sys.exit(1)


def check_helm_installed():
    """helm 설치 확인 (예외 발생 버전)"""
    helm_path = shutil.which("helm")
    if not helm_path:
        logger.error("helm 명령이 시스템에 설치되어 있지 않습니다.")
        raise CliToolNotFoundError("helm", "https://helm.sh/docs/intro/install/")

    try:
        result = subprocess.run(
            ["helm", "version"],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.success(f"helm 확인됨: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        logger.error(f"helm 실행 실패: {e}")
        raise CliToolExecutionError(
            "helm",
            ["helm", "version"],
            e.returncode,
            e.stdout,
            e.stderr,
        )
    except PermissionError:
        logger.error(f"helm 바이너리에 실행 권한이 없습니다: {helm_path}")
        raise CliToolExecutionError(
            "helm",
            ["helm", "version"],
            126,
            None,
            f"Permission denied: {helm_path}",
        )


def check_kubectl_installed_or_exit(
    kubeconfig: str | None = None,
    kubecontext: str | None = None,
):
    """kubectl 설치 확인 (테스트 가능한 버전)"""
    try:
        check_kubectl_installed(kubeconfig, kubecontext)
    except (CliToolNotFoundError, CliToolExecutionError):
        sys.exit(1)


def check_kubectl_installed(
    kubeconfig: str | None = None,
    kubecontext: str | None = None,
):
    """kubectl 설치 확인 (예외 발생 버전)"""
    kubectl_path = shutil.which("kubectl")
    if not kubectl_path:
        logger.error("kubectl 명령이 시스템에 설치되어 있지 않습니다.")
        raise CliToolNotFoundError("kubectl", "https://kubernetes.io/docs/tasks/tools/")

    try:
        cmd = ["kubectl", "version", "--client"]
        if kubeconfig:
            cmd.extend(["--kubeconfig", kubeconfig])
        if kubecontext:
            cmd.extend(["--context", kubecontext])

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.success(f"kubectl 확인됨: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        logger.error(f"kubectl 실행 실패: {e}")
        raise CliToolExecutionError("kubectl", cmd, e.returncode, e.stdout, e.stderr)
    except PermissionError:
        logger.error(f"kubectl 바이너리에 실행 권한이 없습니다: {kubectl_path}")
        raise CliToolExecutionError(
            "kubectl",
            cmd,
            126,
            None,
            f"Permission denied: {kubectl_path}",
        )


def print_helm_connection_help():
    import json
    import os
    import shutil
    import subprocess
    from pathlib import Path

    home = str(Path.home())
    helm_dir = os.path.join(home, ".config", "helm")
    # 0. helm 설치 여부
    if shutil.which("helm") is None:
        logger.error("helm 명령이 시스템에 설치되어 있지 않습니다.")
        logger.info("Helm을 설치하거나, asdf 등 버전 매니저에서 helm 버전을 활성화하세요.")
        logger.info("https://helm.sh/docs/intro/install/")
        return
    # 1. repo 목록
    try:
        result = subprocess.run(
            ["helm", "repo", "list", "-o", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        repos = json.loads(result.stdout)
    except Exception as e:
        logger.warning("helm이 정상적으로 동작하지 않습니다.")
        logger.error(f"에러: {e}")
        logger.info("helm version, helm repo list 명령이 정상 동작하는지 확인하세요.")
        return
    # 2. repo 파일 목록
    try:
        repo_files = []
        if os.path.isdir(helm_dir):
            repo_files = [
                f
                for f in os.listdir(helm_dir)
                if os.path.isfile(os.path.join(helm_dir, f))
            ]
    except Exception:
        repo_files = []
    # 3. 안내 메시지
    if repos:
        logger.info("등록된 helm repo 목록:")
        for repo in repos:
            logger.info(f"  * {repo.get('name', '')}: {repo.get('url', '')}")
        logger.info("helm repo add <name> <url> 명령으로 repo를 추가할 수 있습니다.")
    else:
        logger.info("등록된 helm repo가 없습니다.")
    if repo_files:
        logger.info("~/.config/helm 디렉토리 내 파일:")
        for f in repo_files:
            logger.info(f"  - {f}")
    logger.info("helm version, helm repo list 명령이 정상 동작하는지 확인하세요.")


def print_kube_contexts():
    try:
        result = subprocess.run(
            ["kubectl", "config", "get-contexts", "-o", "name"],
            capture_output=True,
            text=True,
            check=True,
        )
        contexts = result.stdout.strip().splitlines()
        print("사용 가능한 context 목록:")
        for ctx in contexts:
            print(f"  * {ctx}")
        print("kubectl config use-context <context명> 명령으로 클러스터를 선택하세요.")
    except Exception as e:
        print("kubectl context 목록을 가져올 수 없습니다:", e)


def print_kube_connection_help():
    from pathlib import Path

    home = str(Path.home())
    kube_dir = os.path.join(home, ".kube")
    os.path.join(kube_dir, "config")
    # 1. context 목록
    try:
        result = subprocess.run(
            ["kubectl", "config", "get-contexts", "-o", "name"],
            capture_output=True,
            text=True,
            check=True,
        )
        contexts = result.stdout.strip().splitlines()
    except Exception:
        contexts = []
    # 2. ~/.kube 디렉토리 내 파일 목록 (config 제외)
    try:
        files = [
            f
            for f in os.listdir(kube_dir)
            if os.path.isfile(os.path.join(kube_dir, f)) and f != "config"
        ]
    except Exception:
        files = []
    # 3. 안내 메시지
    print("\n⚠️ kubectl이 현재 클러스터에 연결되어 있지 않습니다.")
    if contexts:
        print("사용 가능한 context 목록:")
        for ctx in contexts:
            print(f"  * {ctx}")
        print("kubectl config use-context <context명> 명령으로 클러스터를 선택하세요.")
    else:
        print("사용 가능한 context가 없습니다.")
    if files:
        print("\n~/.kube 디렉토리 내 추가 kubeconfig 파일:")
        for f in files:
            print(f"  - {f}")
        print(
            "\nexport KUBECONFIG=~/.kube/<파일명> 명령으로 해당 클러스터에 연결할 수 있습니다.",
        )
    print("")
