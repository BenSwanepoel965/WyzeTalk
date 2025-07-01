# Wyzetalk
Work done for Wyzetalk during the period of 30 Jun - 18 Jul. 3 folders for 3 projects taken on, listed below.

## 1. Config Linter
Given a .yaml config file, a linter is used to check the validity of the contents inside i.t.o. syntactical and YAML formatting errors, but also config values that are invalid for the SQL template specified by the .yaml file itself.

\n

So far: using a .yaml file (.yamllint) to modify and provide rules used to do format-linting (ie 'stylechecking') of the config .yaml files, implemented in the yamllint() function of config_validator.py. The program will then offer to create a correctly-formatted file for teh user.

\n

Once formatting is deemed to be sufficient, the program will move onto content-linting whereby the type-checking and other content specific linting will take place.

## 2. Report CoPilot
Not yet attempted.
Use current available SQL templates and config files, train an LLM to assist Data Analysts with config file creation, doing 'code completion' and error checking/linting on config files.

## 3. Report Builder
Not yet attempted.
use current available SQL templates and config files, train an LLM to assist Data Analysts with report creation, using text prompts to generate a report.
