import json
import logging
from typing import Any, Dict, List, Optional

from github.GithubObject import NotSet
from pydantic import model_validator
from langchain_core.utils import get_from_dict_or_env
from langchain_community.utilities.github import GitHubAPIWrapper

ISSUE_NUMBER_MUST_BE_SPECIFIED = "issue_number must be specified and must be an integer."


class CustomGitHubAPIWrapper(GitHubAPIWrapper):
    github_access_token: Optional[str] = None

    @classmethod
    @model_validator(mode="before")
    def validate_environment(cls, values: Dict) -> Dict:
        github_access_token = get_from_dict_or_env(
            values, "github_access_token", "GITHUB_ACCESS_TOKEN"
        )

        try:
            from github import Auth, Github
        except ImportError:
            raise ImportError(
                "PyGithub is not installed. "
                "Please install it with `pip install PyGithub`"
            )

        auth = Auth.Token(github_access_token)
        # create a GitHub instance:
        g = Github(auth=auth)
        values["github"] = g
        if values["github_repository"] is not None:
            github_repository = values["github_repository"]
            repo = g.get_repo(github_repository)

            github_base_branch = get_from_dict_or_env(
                values,
                "github_base_branch",
                "GITHUB_BASE_BRANCH",
                default=repo.default_branch,
            )

            active_branch = get_from_dict_or_env(
                values,
                "active_branch",
                "ACTIVE_BRANCH",
                default=repo.default_branch,
            )

            values["github_repo_instance"] = repo
            values["active_branch"] = active_branch
            values["github_base_branch"] = github_base_branch

        return values

    def create_issue(self, issue_query: str) -> str:
        """
        Creates issue for given repository
        Parameters:
            issue_query(str): Contains the issue title and description in json format.
                For example:
                {"title":"Random Issue 2",
                "description":"This is the second of three random issues.",
                "repository_name": "user/repo"}
        Returns:
            A success or failure message
        """
        try:
            logging.info(f"Create issue with {issue_query}")
            issue_data = json.loads(issue_query)
            if "title" not in issue_data:
                raise ValueError("Title field is required for creating new issue")
            issue_title = issue_data.get("title")
            issue_description = issue_data.get("description") if "description" in issue_data else NotSet
            result = self._get_github_repo(issue_data=issue_data).create_issue(title=issue_title,
                                                                               body=issue_description)
            return f"Issue {result} has been added"
        except Exception as e:
            return "Unable to create issue due to error:\n" + str(e)

    def update_issue(self, issue_query: str) -> str:
        """
        Updates issue by number. Supports update operation for title, description, and status.
        :param issue_query: string in json format. For ex.
            {"title":"New Issue 2","description":"This is the new description", "status": "closed"}
        :rtype: :string
        """
        try:
            logging.info(f"Updating issue with {issue_query}")
            issue_data = json.loads(issue_query)
            if "issue_number" not in issue_data and not isinstance(issue_data["issue_number"], int):
                raise ValueError(ISSUE_NUMBER_MUST_BE_SPECIFIED)

            if "state" in issue_data and issue_data["state"] not in ["open", "closed"]:
                raise ValueError("Invalid value for state. It should be 'open' or 'closed'.")

            if len(issue_data) == 1 and "issue_number" in issue_data:
                raise ValueError("At least one additional field (description, title, or state) should be present.")
            issue_number = issue_data.get("issue_number")
            issue_description = issue_data.get("description") if "description" in issue_data else NotSet
            issue_title = issue_data.get("title") if "title" in issue_data else NotSet
            issue_state = issue_data.get("state") if "state" in issue_data else NotSet
            issue = self._get_github_repo(issue_data=issue_data).get_issue(number=issue_number)
            issue.edit(title=issue_title, body=issue_description, state=issue_state)
            return f"Issue {issue_number} has been edited"
        except Exception as e:
            return "Unable to update issue due to error:\n" + str(e)

    def find_issue(self, issue_query: str) -> Dict[str, Any]:
        logging.info(f"Get issue with {issue_query}")
        issue_data = json.loads(issue_query)
        if "issue_number" not in issue_data and not isinstance(issue_data["issue_number"], int):
            raise ValueError(ISSUE_NUMBER_MUST_BE_SPECIFIED)
        issue_number = issue_data.get("issue_number")
        issue = self._get_github_repo(issue_data=issue_data).get_issue(number=issue_number)
        page = 0
        comments: List[dict] = []
        while len(comments) <= 10:
            comments_page = issue.get_comments().get_page(page)
            if len(comments_page) == 0:
                break
            for comment in comments_page:
                comments.append({"body": comment.body, "user": comment.user.login})
            page += 1

        opened_by = None
        if issue.user and issue.user.login:
            opened_by = issue.user.login

        return {
            "number": issue_number,
            "title": issue.title,
            "body": issue.body,
            "comments": str(comments),
            "opened_by": str(opened_by),
        }

    def get_all_issues(self, repository_name: str) -> str:
        """
        Fetches all open issues from the repo excluding pull requests

        Returns:
            str: A plaintext report containing the number of issues
            and each issue's title and number.
        """
        issues = self._get_github_repo(repository_name=repository_name).get_issues(state="open")
        # Filter out pull requests (part of GH issues object)
        issues = [issue for issue in issues if not issue.pull_request]
        if issues:
            parsed_issues = self.parse_issues(issues)
            parsed_issues_str = (
                    "Found " + str(len(parsed_issues)) + " issues:\n" + str(parsed_issues)
            )
            return parsed_issues_str
        else:
            return "No open issues available"

    def comment_on_issue(self, comment_query: str) -> str:
        """
        Adds a comment to a github issue
        Parameters:
            comment_query(str): a string which contains the issue number in json format
        Returns:
            str: A success or failure message
        """
        logging.info(f"Adding comment to issue {comment_query}")
        comment_data = json.loads(comment_query)
        if "issue_number" not in comment_data and not isinstance(comment_data["issue_number"], int):
            raise ValueError(ISSUE_NUMBER_MUST_BE_SPECIFIED)
        if "comment" not in comment_data:
            raise ValueError("comment parameters ")
        issue_number = comment_data.get("issue_number")
        comment = comment_data.get("comment")
        try:
            issue = self._get_github_repo(comment_data).get_issue(number=issue_number)
            issue.create_comment(comment)
            return "Commented on issue " + str(issue_number)
        except Exception as e:
            return "Unable to make comment due to error:\n" + str(e)

    def _get_github_repo(self, issue_data: dict = None, repository_name: str = None):
        if repository_name is not None:
            return self.github.get_repo(repository_name)
        elif "repository_name" not in issue_data:
            raise ValueError("Repository field is required and should be provided for creating new issue")
        else:
            return self.github.get_repo(issue_data.get("repository_name"))

    def create_file(self, file_query: str, commit_message: str = None) -> str:
        """
        Creates a new file on the GitHub repo
        Parameters:
            file_query(str): a string which contains the file path
            and the file contents. The file path is the first line
            in the string, and the contents are the rest of the string.
            For example, "hello_world.md\n# Hello World!"
            commit_message(str): Optional commit message
        Returns:
            str: A success or failure message
        """
        if self.active_branch == self.github_base_branch:
            return (
                "You're attempting to commit to the directly to the"
                f"{self.github_base_branch} branch, which is protected. "
                "Please create a new branch and try again."
            )

        file_path = file_query.split("\n")[0]
        file_contents = file_query[len(file_path) + 2:]

        if commit_message is None:
            commit_message = "Create " + file_path
        else:
            commit_message = commit_message.strip()

        try:
            try:
                file_content = self.github_repo_instance.get_contents(
                    file_path, ref=self.active_branch
                )
                if file_content:
                    return (
                        f"File already exists at `{file_path}` "
                        f"on branch `{self.active_branch}`. You must use "
                        "`update_file` to modify it."
                    )
            except Exception:
                # expected behavior, file shouldn't exist yet
                pass

            self.github_repo_instance.create_file(
                path=file_path,
                message=commit_message,
                content=file_contents,
                branch=self.active_branch,
            )
            return "Created file " + file_path
        except Exception as e:
            return "Unable to make file due to error:\n" + str(e)

    def delete_file(self, file_path: str, commit_message: str = None) -> str:
        """
        Deletes a file from the repo
        Parameters:
            file_path(str): Where the file is
            commit_message(str): Optional commit message
        Returns:
            str: Success or failure message
        """
        if self.active_branch == self.github_base_branch:
            return (
                "You're attempting to commit to the directly"
                f"to the {self.github_base_branch} branch, which is protected. "
                "Please create a new branch and try again."
            )

        if commit_message is None:
            commit_message = "Delete " + file_path
        else:
            commit_message = commit_message.strip()

        try:
            self.github_repo_instance.delete_file(
                path=file_path,
                message=commit_message,
                branch=self.active_branch,
                sha=self.github_repo_instance.get_contents(
                    file_path, ref=self.active_branch
                ).sha,
            )
            return "Deleted file " + file_path
        except Exception as e:
            return "Unable to delete file due to error:\n" + str(e)
