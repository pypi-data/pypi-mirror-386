# Aggregate: daemon temp, live_data.csv and sent_data.csv
Files live_data.csv and sent_data.csv are stored here by workspaces.eds_to_rjn.scripts.daemon_runner main() function.
The daemon can be called like this:
```
poetry run python -m workspaces.eds_to_rjn.scripts.daemon_runner
```
The live_data.csv and sent_data.csv files are registered in the .gitignore for security.
