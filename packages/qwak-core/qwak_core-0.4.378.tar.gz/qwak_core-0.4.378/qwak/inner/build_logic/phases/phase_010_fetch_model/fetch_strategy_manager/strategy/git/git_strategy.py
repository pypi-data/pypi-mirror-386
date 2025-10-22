from __future__ import annotations

import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Union

from qwak.exceptions import QwakException
from qwak.inner.build_logic.interface.build_logger_interface import BuildLogger

from qwak.exceptions import QwakSuggestionException
from qwak.inner.build_logic.tools.files import copytree

try:
    from git import Repo
    from git.exc import GitError
except ImportError:
    pass

from ..strategy import Strategy, get_ignore_pattern


class GitStrategy(Strategy):
    def fetch(
        self,
        src: Union[str, Path],
        dest: str,
        git_branch: str,
        git_credentials: str,
        custom_dependencies_path: str,
        main_dir: str,
        git_ssh_key: str,
        **kwargs,
    ) -> str:
        self.build_logger.debug(f"Fetching Model code from git repository -  {src}")
        with tempfile.TemporaryDirectory() as clone_dest:
            with ssh_key_context(git_ssh_key):
                git_url, git_subdirectory = split_git_url_and_subdirectory(uri=src)
                self.build_logger.debug(
                    f"Fetching model code from git {git_url}, Model located in {git_subdirectory}"
                )
                git_commit_id = self.clone_and_checkout_repo(
                    clone_dest=clone_dest,
                    git_url=git_url,
                    git_branch=git_branch,
                    git_credentials=git_credentials,
                )
                self.copy_model(
                    clone_dest=clone_dest,
                    git_subdirectory=git_subdirectory,
                    model_dest=dest,
                    custom_dependencies_path=custom_dependencies_path,
                    main_dir=main_dir,
                )

        return git_commit_id

    def clone_and_checkout_repo(
        self,
        clone_dest: str,
        git_url: str,
        git_branch: str,
        git_credentials: str,
    ) -> str:
        git_remote_url = get_git_remote_uri(
            self.build_logger,
            url=git_url,
            git_credentials=git_credentials,
        )
        git_commit_id = clone_and_checkout_repo(
            git_repo_url=git_remote_url, to_path=clone_dest, git_branch=git_branch
        )

        return git_commit_id

    def copy_model(
        self,
        clone_dest: str,
        git_subdirectory: str,
        model_dest: str,
        custom_dependencies_path: Optional[str],
        main_dir: str,
    ):
        ignore_patterns, patterns_for_printing = get_ignore_pattern(
            Path(clone_dest) / git_subdirectory, main_dir, self.build_logger
        )
        self.build_logger.debug(
            f"Will ignore the following files: {patterns_for_printing}."
        )

        # Copy model
        copytree(
            src=Path(clone_dest) / git_subdirectory,
            dst=model_dest,
            dirs_exist_ok=True,
            ignore=ignore_patterns,
        )
        self.build_logger.debug("Model copied from git repository")

        # Copy custom dependencies path
        if custom_dependencies_path:
            git_custom_dependencies_path = Path(clone_dest) / Path(
                custom_dependencies_path
            )
            if git_custom_dependencies_path.is_file():
                shutil.copy(
                    src=git_custom_dependencies_path,
                    dst=Path(model_dest) / git_custom_dependencies_path.name,
                )
                self.build_logger.debug(
                    "Custom dependency file copied from git repository"
                )


def split_git_url_and_subdirectory(uri):
    subdirectory = ""
    parsed_uri = uri
    if "#" in uri:
        subdirectory = uri[uri.find("#") + 1 :]
        parsed_uri = uri[: uri.find("#")]
    if subdirectory and "." in subdirectory:
        raise QwakException("'.' is not allowed in project subdirectory paths.")
    return parsed_uri, subdirectory


def get_git_remote_uri(
    build_logger: BuildLogger, url: str, git_credentials: str
) -> str:
    if git_credentials:
        url_start_index = url.find("://") + 3
        url = f"{url[:url_start_index]}{git_credentials}@{url[url_start_index:]}"
    else:
        build_logger.warning("Git credentials secret has been provided")

    return url


@contextmanager
def ssh_key_context(git_ssh_key: str):
    ssh_key_path = None
    if git_ssh_key:
        ssh_key_path = make_ssh_key_file(git_ssh_key)
        add_ssh_file_to_env(ssh_key_path)
    try:
        yield
    finally:
        if ssh_key_path:
            try:
                os.remove(ssh_key_path)
            except OSError as e:
                QwakException(f"Failed to delete ssh key temp key file: {e}")


def make_ssh_key_file(git_ssh_key: str) -> str:
    with tempfile.NamedTemporaryFile(
        delete=False, mode="w", encoding="utf-8"
    ) as temp_file:
        temp_file.write(git_ssh_key + "\n")
    temp_file_path = temp_file.name
    return temp_file_path


def add_ssh_file_to_env(ssh_key_file_path: str) -> None:
    os.environ["GIT_SSH_COMMAND"] = (
        f"ssh -i {ssh_key_file_path} -o StrictHostKeyChecking=no"
    )
    os.environ["GIT_SSH"] = f"ssh -i {ssh_key_file_path} -o StrictHostKeyChecking=no"


def clone_and_checkout_repo(git_repo_url: str, to_path: str, git_branch: str) -> str:
    try:
        repo = Repo.clone_from(url=git_repo_url, to_path=to_path)
        repo.submodule_update(init=True, recursive=True)
        if git_branch in repo.branches:
            repo.git.checkout(git_branch)
        else:
            repo.git.checkout("-b", git_branch, f"{repo.remote()}/{git_branch}")
        return repo.head.object.hexsha
    except GitError as e:
        raise QwakSuggestionException(
            src_exception=e,
            message="Unable to clone git repository",
            suggestion="Please check you git credentials",
        )
