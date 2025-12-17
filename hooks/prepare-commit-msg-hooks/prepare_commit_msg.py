#!/usr/bin/env python3

import json
import sys
import os
import textwrap
from tkinter import W

import ollama

LINE_LENGTH = 79
DEBUG_FLAG = "DEBUG_GITHOOKS"
LLM_MODEL_ENV_VAR="OLLAMA_LLM_MODEL"
LLM_HOST_ENV_VAR="OLLAMA_HOST"

DEFAULT_LLM_MODEL="llama3.1"
DEFAULT_LLM_URL="http://localhost:11434"

SYSTEM_PROMPT="""
You are helpful assistant of the software developer. Your job is to analyze
changes which are going to be commited to the project's repository and based
on that propose some initial commit message draft.

<rules>
- user message contains always 2 things:
    - branch name inside <branch></branch> tags,
    - diff which is going to be commited, inside <diff></diff> tags,

- your proposal of the commit message have to always be in english language
  only,
- you have to propose commit message in three parts:
    - commit_msg_title - this is what will be placed as first line of the
      git commit message and is always mandatory,
    - commit_msg - this is part with detailed description of the change,
      it is optional, you can omit it sometimes if changes are small and
      self-explanatory,
    - related issue - this should contain number of the related bug or new
      feature from some bug tracking system, it is optional, put empty string
      if you will not find anything like that,
- your proposal of the commit message have to be as short as possible, not
  longer then it is really needed,

- your response have to be in JSON format, with schema like below:
    {
        "_reasoning": "put your thinking here, for debugging purpose",
        "commit_msg_title": "Title of the commit message you propose",
        "commit_msg": "The rest of the commit message you propose"
    }
</rules>

<examples>
    <example>
        <input>
            <diff>
                diff --git a/file1.txt b/file1.txt
                index 1234567..89abcdef 100644
                --- a/file1.txt
                +++ b/file1.txt
                @@ -1,1 +1,1 @@
                -def test_method()
                +def better_test_method()
            </diff>
            <branch>
            issue/123454
            </branch>
        </input>
        <output>
        {
            "_reasoning": "your reasoning, with detailed description how you "
                          "have came to the final conclusion",
            "commit_msg_title": "Replace test_method with new implementation",
            "commit_msg": "This patch replaces old test_method with new one, named better_test_method.",
            "related_issue": "1234567"
        }
        </output>

    </example>
</examples>

"""


def is_debug_enabled():
    debug_flag = os.environ.get(DEBUG_FLAG, "")
    return debug_flag.lower() in ["1", "yes", "true"]


def get_llm_model():
    llm_model = os.environ.get(LLM_MODEL_ENV_VAR, DEFAULT_LLM_MODEL)
    if not llm_model:
        return DEFAULT_LLM_MODEL
    return llm_model


def get_llm_url():
    llm_host = os.environ.get(LLM_HOST_ENV_VAR, DEFAULT_LLM_URL)
    if not llm_host:
        llm_host = DEFAULT_LLM_URL
    return f"http://{llm_host}"


def get_args():
    if len(sys.argv) < 4:
        # no diff or commit message file provided, nothing to do
        exit(0)
    commit_msg_file = sys.argv[1]
    if not commit_msg_file:
        # no commit message file provided, nothing to do
        exit(0)
    git_branch = sys.argv[2]
    diff = sys.argv[3]
    if not diff:
        # no diff provided, nothing to do
        exit(0)
    return commit_msg_file, git_branch, diff


def prepare_commit_msg_draft(title, content, related_issue):
    commit_msg = f"""
#### This is just draft of the commit msg made by AI ####

{title}"""
    if content:
        commit_msg = f"{commit_msg}\n"
        wrapped_content = textwrap.wrap(content, LINE_LENGTH)
        for line in wrapped_content:
            commit_msg = f"{commit_msg}\n{line}"
    if related_issue:
        commit_msg = f"{commit_msg}\n\nCloses: #{related_issue}"
    return commit_msg


def prepare_commit_msg_file(file_path, commit_msg):
    with open(file_path, "a") as f:
        f.seek(0)
        f.write(commit_msg)


def main():

    commit_msg_file, git_branch, diff = get_args()
    input_msg = f"<branch>{git_branch}</branch><diff>{diff}</diff>"

    client = ollama.Client(host=get_llm_url())
    llm_response: ollama.ChatResponse = client.chat(
        model=get_llm_model(),
        stream=False,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": input_msg
            }
        ]
    )

    try:
        response_json = json.loads(llm_response.message.content)
    except json.JSONDecodeError:
        if is_debug_enabled():
            print(f"Error: Invalid JSON response: {llm_response.message.content}")
        # Don't block commit if JSON is not valid
        exit(0)

    if is_debug_enabled():
        print("--------------------------------")
        print(f"Reasoning: {response_json['_reasoning']}")
        print("--------------------------------")

    commit_msg = prepare_commit_msg_draft(
        response_json['commit_msg_title'],
        response_json.get('commit_msg', ''),
        response_json.get('related_issue', ''))

    prepare_commit_msg_file(commit_msg_file, commit_msg)


if __name__ == "__main__":
    main()
