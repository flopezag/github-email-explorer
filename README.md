## github-email-explorer

<!--[![Code Climate](https://codeclimate.com/github/flopezag/github-email-explorer/badges/gpa.svg)](https://codeclimate.com/github/flopezag/github-email-explorer) -->

For people who want to create an email marketing plan for particular group on 
GitHub, github-email-explorer can collect addresses from a repository you want, 
and then send email content to those email addresses.

### Installation

```bash
pip install github-email-explorer
```

There are two commends can be used in github-email-explorer,

* ```ge-explore```: Get email address list from stargazers, forks or watchers on a repository
* ```ge-sendgrid```: Send email by list or repository name with SendGrid API

SendGrid is only one email provider at current progress.

### Example of Getting Email Addresses from Stargazers, Forks or Watchers

#### A. Using Command

```bash
$ ge-explore --repo flopezag/github-email-explorer --action_type star fork watch
 
John (john2) <John@example.org>; Peter James (pjames) <James@example.org>;
```

You can get user email by ```ge-explore``` with ```<owner>/<repo>```. The email 
addresses are responded in a formatted string. You can copy contact list to any 
email service you have, then send your email with those contact address.

(If you encounter the situation of limitation from GitHub server during running 
the command, please add ```--client_id <your_github_auth_id> --client_secret <your_github_auth_secret>``` 
with the command above. Get *Client ID* and *Client Secret* by [OAuth applications].)

#### B. Using Python Script

```python
from github_email_explorer import github_email

ges = github_email.collect_email_info('flopezag', 'github-email-explorer', ['star', 'watch'])

for ge in ges:
    print(f'{ge.g_id} -> {ge.name}, {ge.email}')

# With Authentication
# github_api_auth = ('<your_client_id>', '<your_client_secret>')
# ges = github_email.collect_email_info('flopezag', 'github-email-explorer', ['star', 'watch'],
#                                        github_api_auth=github_api_auth)
```

```bash
$ python examples/get_email.py

0john123 -> P.J. John, john@example.org
pjames56 -> Peter James, james@example.org
```

You can find get_email.py in *examples* folder.

### How to Send a Email to GitHub Users from a Particular Repository?

#### 1. Write Email Content with Template Format

The [Jinja2] is used to render email content in github-email-explorer, basic 
[expressions] make email content more flexible for personal information.

Here is an example to use following syntax, the file saved to ```examples/marketing_email.txt```

```
subject: Thanks for using {{repository}}
from: test@example.com
user:
repository: flopezag/github-email-explorer
repository_owner: flopezag
repository_name: github-email-explorer
site: GitHub

<p>Hi {{ user.name }} ({{ user.g_id }}),</p>
<p>Thank you for trying {{ repository_owner }}/{{ repository_name }}!</p>

<p>...</p>

<p>I look forward to seeing you on GitHub :)</p>
<p>flopezag</p>
```

| Metadata Field   | Description                                                                                                                                                                                                                                                                                        |
|------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| subject          | email subject                                                                                                                                                                                                                                                                                      |
| from             | sender address                                                                                                                                                                                                                                                                                     |
| from_name        | sender name                                                                                                                                                                                                                                                                                        |
| user             | you can put an email list with a well format for parse user's ```name``` and ```g_id```. For example, ```John (john2) <John@example.org>; Peter James (pjames) <James@example.org>```. If you don't put an email list, the repository field will be used for running ge-explore to get email list. |
| repository       | full repository name on GitHub                                                                                                                                                                                                                                                                     |
| repository_owner | repository owner                                                                                                                                                                                                                                                                                   |
| repository_name  | repository name                                                                                                                                                                                                                                                                                    |

```site``` is not a essential field, it will be in SendGrid custom_args field for log

You can use syntax ```{{ ... }}``` to substitute metadata field in runtime stage for personal information.

#### 2. Send Email

In order to send email to many users flexibly, we combine the email list from 
result of ge-explore and SendGrid to approach it.

```
ge-sendgrid --api_key <your_sendgrid_api_key> 
            --template_path <github-email-explorer_folder_path>/examples/marketing_email.txt
```

<!--
The following image is a real example of email format for ge-sendgrid command.

> <img src="examples/marketing_email.png" width="300">
-->

### More...

In order to understand API [rate limit] you are using, the status information 
can be found by github-email-explorer command.

Without authentication

```bash
$ ge-explore --status

Resource Type      Limit    Remaining  Reset Time
---------------  -------  -----------  --------------------
Core                  60           60  2016-07-07T04:56:12Z
Search                10           10  2016-07-07T03:57:12Z
```

With authentication

You can request more than 60 using authentication by [OAuth applications]

```bash
$ ge-explore --status --client_id <your_github_auth_id> --client_secret <your_github_auth_secret>

== GitHub API Status ==
Resource Type      Limit    Remaining  Reset Time
---------------  -------  -----------  --------------------
Core                5000         5000  2016-07-06T07:59:47Z
Search                30           30  2016-07-06T07:00:47Z
```


[rate limit]:https://developer.github.com/v3/rate_limit/
[OAuth applications]:https://github.com/settings/developers
[Jinja2]:http://jinja.pocoo.org/
[expressions]:http://jinja.pocoo.org/docs/dev/templates/#expressions
