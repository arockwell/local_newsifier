You'll implement a feature based on a specified GitHub issue.

If an issue number is provided as an argument (e.g., project:implement 233):
- Focus on implementing that specific issue
- Use "gh issue view $ARGUMENTS" to get the full issue details
- Create a branch named "issue-$ARGUMENTS-implementation" for your work

If no issue number is provided:
- Make sure you are on a branch immediately off of a freshly pulled main
- You should have a plan already in your context that you need to implement

This is the ground rules for implementing:

PUSH THE FIRST COMMIT AND MAKE A PR IMMEDIATELY

use the gh pr command on the cli to interface with github

Commit early, commit often

Before you push, TEST THE CODE

use poetry to test the code.

TEST THE CODE FIRST.

Once the tests are working, PUSH.

You need to monitor the PR until it completes. This can take up to five minutes.

PLEASE WAIT FIVE MINUTES BEFORE ALERTING ME. I KNOW THAT'S A LONG TIME. YOU CAN DO IT!

If the build is failing, alert me with a plan for how to fix the build.

NOTE, if you don't see the tests start, you probably need to resolve conflicts with main.

This is something you will want to check for. I can't merge your work otherwise!