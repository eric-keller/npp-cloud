# Overview

Utility to perform some checks for the coursera module 2 lab 1.

Note: This is still in development, so has only been lightly tested for module 2 so far.

# To run

```
python3 cloud-extract.py <module> <json_file>
```

The module will be mod2 or mod3 (future), and the checks will be performed based on what's expected for each.

The json_file is the json output of terraform show.  For example:

```
terraform show --json > terraform_show_output.json
```




