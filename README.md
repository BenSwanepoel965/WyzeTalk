# Wyzetalk

Work done for Wyzetalk during the period of 30 Jun - 18 Jul.

## 1. Config Linter

Given a .yaml config file, a linter is used to check the validity of the contents inside i.t.o. syntactical and YAML formatting errors, but also config values that are invalid for the SQL template specified by the .yaml file itself, by Wyzetalk standards.

The .yamllint file is used to tweak and alter the formatting rules used to check the validity of the provided .yaml file. Based off of the errors provided, the linter will then make passes through the erroneous file and attempt to fix them. After each pass, the formatting check is run again afterwhich the linting process proceeds again if errors are still present.

Currently, as of 09/18/2025, the linter is able to fix the following syntactical formatting errors:

1. General indentation
2. Spacing before and after colons
3. Trailing spaces at end of lines
4. Missing '---' at the start of the document
5. Line length - set at 120 characters but brought up as warning.

As mentioned, these checks can be disabled. Other formatting rules can be altered as well, please refer to the yamllint documentation for a full breakdown of all the rules (https://yamllint.readthedocs.io/en/stable/rules.html).

To run this whenever you save a .yaml file you will need to install the Emeraldwalk RunOnSave extension in VSCode (https://marketplace.visualstudio.com/items?itemName=emeraldwalk.RunOnSave). Then add the following section to your user settings.json file (accessed through <CTRL + P> and searching for it in the popup bar)

```json
"emeraldwalk.runonsave": {
    "commands": [
      {
        "match": "\\.ya?ml$",
        "cmd": "python ${workspacefolder}\\1. Config Linter\\linter.py ${file}"
      }
    ]
  }
```

As with the yamllint documentation, there is many ways to customise how you wish your EmeraldWalk to execute. Please refer to the documentation for more information.

Once syntactical formatting is deemed to be sufficient or it reaches a collection of errors it cannot fix, the program will move onto semantical content-linting whereby the type-checking and other content specific linting will take place. This is done using predetermined schema, 1 for the general file (i.e. the 'dag' and the 'ouput' section) and 1 for the sql_params section specific to the sql template listed before it in the inputs.sql_template field.

The output (in the output panel) will be of the following form:

<!-- Fix the <> in the following 2 points. they are not rendering as intended on GitHub-->

1. [error] Field '<field in .yaml file>' should be '<<expected type>>', got '<found type>'. 
2. [info] '<field in SQL template file>' was found in the SQL template/schema but not in the config file.





<!--  ## 2. Report CoPilot

Not yet attempted.
Use current available SQL templates and config files, train an LLM to assist Data Analysts with config file creation, doing 'code completion' and error checking/linting on config files.

## 3. Report Builder

Not yet attempted.
use current available SQL templates and config files, train an LLM to assist Data Analysts with report creation, using text prompts to generate a report. -->
