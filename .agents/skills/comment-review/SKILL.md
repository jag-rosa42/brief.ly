---
name: comment-review
description: Review a GitHub pull request and optionally publish precise inline review comments using the GitHub CLI. Use when the user asks to review a PR, review commits from a PR, or post review findings to GitHub.
---

# GitHub PR review

Use `gh` for GitHub access.
The user must specify a review configuration.

Example:
`$comment-review Review PR 123 using arnaubot.md`


The review configuration must be loaded only from the `references/` directory.

Do not load review configurations from arbitrary paths.

If the requested configuration isn't specified or does not exist in `references/`, stop the review and ask the user to specify an existing configuration.


## Review

1. Read the requested configuration file before reviewing the PR.

2. Treat its rules as review criteria.

3. Identify the PR:
   `gh pr view <PR> --json number,title,body,baseRefName,headRefName,headRefOid`

4. Fetch the diff:
   `gh pr diff <PR>`

5. Inspect relevant surrounding source code when necessary.

6. Each findings must end with the review configuration name.
Example:
`Author: arnaubot`

Do not report:
- issues already caught deterministically by lint/formatters

For each finding produce:
- path
- changed line
- concise explanation

Only comment on lines present in the PR diff.

## Publishing

Never publish comments unless the user explicitly requests it.

Before publishing, verify that the PR HEAD SHA has not changed since the
review was performed.

Publish all findings as a single GitHub review using:

`gh api --method POST repos/{owner}/{repo}/pulls/{pr}/reviews`

The request body must be valid JSON with this structure:

  {
    "commit_id": "<verified PR HEAD SHA>",
    "body": "<review summary>",
    "event": "COMMENT",
    "comments": [
      {
        "path": "<repository-relative path>",
        "line": <integer>,
        "side": "RIGHT",
        "body": "<finding>\n\nAuthor: <configuration name>"
      }
    ]
  }

  For side: Use `RIGHT` for additions or context lines and `LEFT` for deletions.
  For multi-line comments, also provide `start_line` and `start_side`.
  Pass the serialized payload through `gh api --input -`.

Use event `COMMENT` unless the user explicitly requests APPROVE or
REQUEST_CHANGES.
