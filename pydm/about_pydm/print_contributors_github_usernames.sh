# grabs all the github usernames of contributors and prints them sorted alphabetically with @ prepended.
# we can copy the output and use to update contributors.txt
# (will have to increase 'per_page=200' if we ever get over 200 contributors)
curl -s https://api.github.com/repos/slaclab/pydm/contributors?per_page=200 | jq -r '.[] | "@" + .login' | sort

