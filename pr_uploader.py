import json
import os
import sys
from email.utils import parsedate_to_datetime
import requests
from github import Github

MAX_RANGE_FOR_SEARCHING = 50


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def find_root_commit_index_for_target_branch(target_commits, base_commits):
    for b_i in range(0, max(MAX_RANGE_FOR_SEARCHING, base_commits.totalCount)):
        for t_i in range(0, max(MAX_RANGE_FOR_SEARCHING, target_commits.totalCount)):
            if base_commits[b_i].sha == target_commits[t_i].sha:
                return t_i
    return -1


def make_pr_message(commit_message):
    messages = commit_message.split("\n")
    result = None
    for message in messages:
        message = message.strip()
        if message:
            if result:
                if message.startswith("-") or message.startswith("*"):
                    result = f"{result}\n    {message}"
                else:
                    result = f"{result}\n    - {message}"
            else:
                result = f"- [x] {message}"
    return result

print("""

┏━━━┳━━━┓┏┓╋┏┳━━━┳┓╋╋┏━━━┳━━━┳━━━┳━━━┳━━━┓
┃┏━┓┃┏━┓┃┃┃╋┃┃┏━┓┃┃╋╋┃┏━┓┃┏━┓┣┓┏┓┃┏━━┫┏━┓┃
┃┗━┛┃┗━┛┃┃┃╋┃┃┗━┛┃┃╋╋┃┃╋┃┃┃╋┃┃┃┃┃┃┗━━┫┗━┛┃
┃┏━━┫┏┓┏┛┃┃╋┃┃┏━━┫┃╋┏┫┃╋┃┃┗━┛┃┃┃┃┃┏━━┫┏┓┏┛
┃┃╋╋┃┃┃┗┓┃┗━┛┃┃╋╋┃┗━┛┃┗━┛┃┏━┓┣┛┗┛┃┗━━┫┃┃┗┓
┗┛╋╋┗┛┗━┛┗━━━┻┛╋╋┗━━━┻━━━┻┛╋┗┻━━━┻━━━┻┛┗━┛
""")

with open(resource_path("./environment.json")) as json_file:
    json_config = json.load(json_file)
    GITHUB_USER_TOKEN = json_config["github_user_token"]
    GITHUB_USER_NAME = json_config["github_user_name"]
    GITHUB_API_HOST = json_config["github_api_host"]
    DEFAULT_REPOSITORY_NAME = json_config["default_repository_name"]
    DEFAULT_REVIEWER_NAMES = json_config["default_reviewer_names"]
    DEFAULT_ASSIGNEE_NAMES = json_config["default_assignee_names"]
    DEFAULT_PR_TEMPLATE = json_config["default_pr_template"]

g = Github(base_url=GITHUB_API_HOST, login_or_token=GITHUB_USER_TOKEN)
g_repo = g.get_repo(DEFAULT_REPOSITORY_NAME)
current_branches = g_repo.get_branches()
sorted_current_branches = sorted(current_branches, key=lambda branch: parsedate_to_datetime(
    branch.commit.commit.last_modified), reverse=True)
sorted_current_branch_names = [sorted_current_branches[x].name for x
                               in range(0, len(sorted_current_branches))]

print(f"Repo loaded : {g_repo}")
print("--------------")
print("-Remote branches-")
print(sorted_current_branch_names)
base_branch = None
while base_branch not in sorted_current_branch_names:
    base_branch = input(f"\nEnter base branch on your remote repo [{g_repo.default_branch}]: ")
    if not base_branch:
        base_branch = g_repo.default_branch
    if base_branch not in sorted_current_branch_names:
        print("Wrong branch name.")
print(f"Base branch: {base_branch}")

print("--------------")
print("-Remote branches-")
print(sorted_current_branch_names)
target_branch = None
while (target_branch not in sorted_current_branch_names) or target_branch == base_branch:
    target_branch = input(
        f"\nEnter target branch on your remote repo [{sorted_current_branch_names[0]}]: ")
    if not target_branch:
        target_branch = sorted_current_branch_names[0]
    if target_branch not in sorted_current_branch_names:
        print("Wrong branch name.")
    if target_branch == base_branch:
        print("Target branch can not be same with base branch.")
print(f"Target branch: {target_branch}")
print("--------------")

base_branch_commits = g_repo.get_commits(sha=base_branch)
target_branch_commits = g_repo.get_commits(sha=target_branch)

root_index = find_root_commit_index_for_target_branch(target_branch_commits, base_branch_commits)
if root_index == -1:
    print(f"There is no root commit on your {base_branch} branch for {target_branch} branch")
    exit(0)
elif root_index == 0:
    print(f"There is no new commit from base branch({base_branch})")
    exit(0)

filtered_target_branch_commits = list(target_branch_commits[0:root_index])

resultMessage = "\n".join(
    [(make_pr_message(filtered_target_branch_commits[i].commit.message)) for i in
     range(0, root_index)])
resultMessage = DEFAULT_PR_TEMPLATE.format(message=resultMessage)

default_title = filtered_target_branch_commits[-1].commit.message.split("\n")[0]
print("-Your commit headers-")
for commit_parent in filtered_target_branch_commits:
    print(commit_parent.commit.message.split("\n")[0])
pr_title = input(
    f'\nInput PR title[{default_title}]: ')
if not pr_title:
    pr_title = default_title

print("--------------")
print("Your PR Title :")
print(pr_title)
print("\nYour PR Message :")
print(resultMessage)
print("--------------")

found_assignees = []
for assignee in list(g_repo.get_assignees()):
    if assignee.login in DEFAULT_ASSIGNEE_NAMES:
        found_assignees.append(assignee)
if len(found_assignees) == 0:
    print("There is no any assignees who are in the environment.json")
    exit(1)

milestones = list(g_repo.get_milestones())

if len(milestones) == 0:
    print("There is no milestone...")
print("Milestone")
print("\n".join([f"{i + 1}. {milestone}" for i, milestone in enumerate(milestones)]))
milestone_no = "-1"
selected_mile_stone = None
while milestone_no and (not milestone_no.isdigit()
                        or int(milestone_no) > len(milestones)
                        or int(milestone_no) <= 0):
    milestone_no = input("Select milestone : ")
milestone_no = int(milestone_no) - 1

print("--------------")
print("Your PR Title :")
print(pr_title)
print("\nYour PR Message :")
print(resultMessage)
print("\nAssignees :")
print(found_assignees)
print("\nReviewers :")
print(DEFAULT_REVIEWER_NAMES)
if milestone_no:
    selected_mile_stone = milestones[milestone_no]
    print("\nMilestone :")
    print(selected_mile_stone)
print("--------------")
y_or_n = None
while not y_or_n:
    y_or_n = input("Are you sure? (Y/N) : ")
    if y_or_n != 'y' and y_or_n != "Y" and y_or_n != "n" and y_or_n != "N":
        y_or_n = None
if y_or_n == 'n' or y_or_n == 'N':
    exit(0)

made_pr = g_repo.create_pull(pr_title, resultMessage, base_branch, target_branch)
made_pr.add_to_assignees(*found_assignees)
made_pr.create_review_request(DEFAULT_REVIEWER_NAMES)
if selected_mile_stone:
    requests.patch(f"{GITHUB_API_HOST}/repos/{DEFAULT_REPOSITORY_NAME}/issues/{made_pr.number}",
                   data=json.dumps({'milestone': selected_mile_stone.number}),
                   auth=(GITHUB_USER_NAME, GITHUB_USER_TOKEN))
