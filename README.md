# GitAutomator
Do not waste your time on repeated Git or Github jobs.
Automate your git flow!

# features
* [pr_uploader.py](pr_uploader.py) : Upload your pull request with title and message which are made automatically based on commit messages.
* push_with_rebase.py : Comming soon

# How to use

## pr_uploader.py
* Download zip from [releases](https://github.com/LakeLab/GitAutomator/releases)
* Fill the context on [environment.json](environment.json) file
* Execute pr_uploader!


---
# ETC

#### Required permission scope list for pr_uploader.py on github_user_token
* repo (all permissions)
* admin:org 
    * read:org 


#### Caution for pyinstaller
You need to make an executable file with pyinstaller as follow.\
```pyinstaller pr_uploader.py --add-data 'environment.json:.' --hidden-import=_cffi_backend```
