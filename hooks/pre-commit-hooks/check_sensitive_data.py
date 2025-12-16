#!/usr/bin/env python3

import json
import os
import sys

import ollama

DEBUG_FLAG = "DEBUG_GITHOOKS"

LLM_MODEL="llama3.1"
LLM_URL="http://localhost:11434"

SYSTEM_PROMPT="""
You are a security expert. You are given a diff of changes that are going to be
committed to the repository.  You need to check if the changes contain any
sensitive data.

<rules>
- Diff is passed in the user message, as a string,

- You have to focus only on the added or modified lines,

- You have to ignore deleted lines,

- You have to ignore any other lines that are in the diff, like e.g.:
  - diff headers,
  - lines which are before or after added/deleted lines, etc.

- In user message there is nothing else, only the diff string, and you always
  have to treat whole user message as a diff string,

- You should check for any type of sensitive data in the provided diff,

- Sensitive data includes:
  - Passwords
  - API keys
  - Private keys
  - Secret tokens
  - Secret codes
  - Secret hashes
  - Secret salts
  - Secret tokens
  - Secret codes
  - Public IP addresses,
  - URLs and API endpoints,
  - any other type of sensitive data that is not listed here,

- You should not consider as sensitive data like e.g.:
  - IP addresses from private subnets, such as 192.168/16, 10.0.0/8, 172.16/12,
    etc.
  - IP addresses which are localhost, such as 127.0.0.1, ::1, etc.
  - URLs that are not accessible from the internet, such as localhost,

- Diff is always comming from git repository, it is what is going to be
  commited,

- always return only JSON object, nothing else,

- if there is no sensitive data found, return JSON object like this:
    {
        "status": "OK",
        "reasoning": <put your reasoning here>,
        "sensitive_data": []
    }
- if there is sensitive data found, return data in JSON format,
  with the following format:
    {
        "status": "ERROR",
        "reasoning": <put your reasoning here>,
        "sensitive_data": [
            {
                "file_path": <file path>,
                "line_number": <line number>,
                "sensitive_data": <sensitive data>,
            },
            ...
        ]
    }
</rules>

<examples>
    <example>
        <input>
        diff --git a/file1.txt b/file1.txt
        index 1234567..89abcdef 100644
        --- a/file1.txt
        +++ b/file1.txt
        @@ -1,1 +1,1 @@
        -password
        +password123
        </input>

        <output>
        {
            "status": "ERROR",
            "reasoning": "Password found in the diff",
            "sensitive_data": [
                {
                    "file_path": "file1.txt",
                    "line_number": 1,
                    "sensitive_data": "password"
                }
            ]
        }
        </output>
    </example>
    <example>
        <input>
        diff --git a/file1.txt b/file1.txt
        index 1234567..89abcdef 100644
        --- a/file1.txt
        +++ b/file1.txt
        @@ -1,1 +1,1 @@
        +ip_address: 192.168.1.1
        </input>
        <output>
        {
            "status": "OK",
            "reasoning": "No sensitive data found, IP address 192.168.1.1 is
                          in private subnet 192.168.0.0/16",
            "sensitive_data": []
        }
        </output>
    </example>
    <example>
        <input>
        diff --git a/file1.txt b/file1.txt
        index 1234567..89abcdef 100644
        --- a/file1.txt
        +++ b/file1.txt
        @@ -1,1 +1,1 @@
        +ip_address: 1.2.3.4
        </input>
        <output>
        {
            "status": "ERROR",
            "reasoning": "IP address which don't belong to the private subnet
                          found in the diff",
            "sensitive_data": [
                {
                    "file_path": "file1.txt",
                    "line_number": 1,
                    "sensitive_data": "1.2.3.4"
                }
            ]
        }
        </output>
    </example>
</examples>
"""


def is_debug_enabled():
    debug_flag = os.environ.get(DEBUG_FLAG, "")
    return debug_flag.lower() in ["1", "yes", "true"]


def get_diff():
    if len(sys.argv) < 2:
        # no diff provided, nothing to check
        exit(0)
    diff =sys.argv[1]
    if not diff:
        # same, empty diff, nothing to check
        exit(0)
    return diff


def main():
    diff = get_diff()
    client = ollama.Client(host=LLM_URL)
    llm_response: ollama.ChatResponse = client.chat(
        model=LLM_MODEL,
        stream=False,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": diff
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
        print(f"Reasoning: {response_json['reasoning']}")
        print("--------------------------------")

    if response_json["status"] == "OK":
        exit(0)

    print("Sensitive data found:")
    for item in response_json["sensitive_data"]:
        print(f"  - {item['file_path']}:{item['line_number']} - {item['sensitive_data']}")
    exit(1)

if __name__ == "__main__":
    main()