# Wyzetalk

Work done for Wyzetalk during the period of 30 Jun - 18 Jul. 3 folders for 3 projects taken on, listed below.

## 1. Config Linter

Given a .yaml config file, a linter is used to check the validity of the contents inside i.t.o. syntactical and YAML formatting errors, but also config values that are invalid for the SQL template specified by the .yaml file itself.

The .yamllint file is used to tweak and alter the formatting rules used to check the validity of the provided .yaml file. Based off of the errors provided, the linter will then make passes through the erroneous file and attempt to fix them. After each pass, the formatting check is run again afterwhich the linting process proceeds again if errors are still present.

Currently, the linter is able to fix the following formatting errors: 1. Indentation 2. Spacing before and after colons 3. Trailing spaces at end of lines 4. Missing '---' at the start of the document 5. Line-length (set at 120 characters)

Once formatting is deemed to be sufficient, the program will move onto content-linting whereby the type-checking and other content specific linting will take place.

## 2. Report CoPilot

Not yet attempted.
Use current available SQL templates and config files, train an LLM to assist Data Analysts with config file creation, doing 'code completion' and error checking/linting on config files.

## 3. Report Builder

Not yet attempted.
use current available SQL templates and config files, train an LLM to assist Data Analysts with report creation, using text prompts to generate a report.
