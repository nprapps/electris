app-template
============

This is a rough start at something.

Copy it for your projects.

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