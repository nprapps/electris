app-template
============

This is a rough start at something.

First, set up an empty git repo for your project.

Now, copy the code in...
```
git clone git@github.com:npr/app-template.git NAME_OF_NEW_PROJECT_REPO
cd NAME_OF_NEW_PROJECT_REPO
git remote rm origin
git remote add origin URL_TO_A NEW_GITHUB_REPO
git push -u origin master
```

Set up a virtualenv, install the requirements, and go nuts.
```
mkvirtualenv your-project-name
pip install -r requirements.txt
```

Set the project_name in the fabfile.

To deploy, you'll need s3cmd installed and configured w/ the Amazon keys.
```
fab stage master deploy
```