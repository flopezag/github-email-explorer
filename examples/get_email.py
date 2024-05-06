from github_email_explorer import github_email
from config.config import API_TOKEN

# With Authentication
ges = github_email.collect_email_info(repo_user_id='FIWARE',
                                      repo_name='context.Orion-LD',
                                      actions=['contributor'],
                                      github_api_auth=API_TOKEN)

for ge in ges:
    print(f"{ge.g_id} -> {ge.name}, {ge.email}")
