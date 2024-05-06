# -*- coding: utf-8 -*-

from collections import OrderedDict
from requests.exceptions import HTTPError
from requests import get
from github_email_explorer.api_url import GitHubEndPoint as EndPoint
from re import compile, IGNORECASE
from math import ceil
from time import sleep
from github_email_explorer.fiware_catalogue import Catalogue
from config.config import API_TOKEN


class GithubUserEmail(object):
    def __init__(self, *args, **kwargs):
        self.g_id = None
        self.name = kwargs.get('name', None)
        self.email = kwargs.get('email', None)
        self.from_profile = kwargs.get('from_profile', None)
        if len(args) > 0 and (type(args[0]) is tuple):
            self.name = args[0][0]
            self.g_id = args[0][1]
            self.email = args[0][2]
            self.from_profile = args[0][3]


class GithubAPIStatus(object):
    def __init__(self):
        self.core_limit = None
        self.core_remaining = None
        self.core_reset_time = None
        self.search_limit = None
        self.search_remaining = None
        self.search_reset_time = None


class GithubRepository(object):
    def __init__(self):
        self.repo_id = None
        self.name = None
        self.description = None
        self.stargazers_count = 0
        self.watchers_count = 0
        self.forks_count = 0


def select_end_point_builder(act_type):
    return {
        'star': EndPoint.stargazers,
        'fork': EndPoint.forks,
        'watch': EndPoint.watchers,
        'contributor': EndPoint.contributors
    }[act_type]


def select_action_count(github_repo, action_type):
    result: int = 0

    match action_type:
        case 'star':
            result = github_repo.stargazers_count
        case 'fork':
            result = github_repo.forks_count
        case 'watch':
            result = github_repo.watchers_count
        case 'contributor':
            result = len(github_repo.contributors)
        case _:
            print(f'ERROR, unexpected action type "{action_type}"')

    return result


def integrate_user_ids(user_id, repo, actions, github_api_auth):
    user_ids: list = []

    for action_type in actions:
        # get repo
        github_repo = repository(user_id=user_id, repo=repo, github_api_auth=github_api_auth)

        # pagination
        per_page = 100
        total_pages = ceil(select_action_count(github_repo=github_repo, action_type=action_type) / per_page)

        # create url
        url = select_end_point_builder(action_type)(user_id, repo)

        # get id by rolling pages
        user_ids = user_ids + request_user_ids_by_roll_pages(url, github_api_auth, total_pages, per_page)

    return OrderedDict.fromkeys(user_ids).keys()


def request_user_ids_by_roll_pages(url, github_api_auth, total_pages, per_page):
    # loop page with url
    user_ids = []
    for i in range(0, total_pages + 1):
        url = EndPoint.pagination(url, page=(i + 1), per_page=per_page)
        # r = requests.get(url)
        r = get_operation(url, github_api_auth)

        # raise error when found nothing
        r.raise_for_status()

        # handling result
        user_ids = user_ids + [info['login'] if 'login' in info else info['owner']['login'] for info in r.json()]

    return user_ids


def collect_email_info(repo_user_id, repo_name, actions, github_api_auth=None):
    # get user ids
    user_ids = integrate_user_ids(repo_user_id, repo_name, actions, github_api_auth)

    # get and return email info
    return users_email_info(user_ids, github_api_auth)


def users_email_info(action_user_ids, github_api_auth):
    ges = []
    for user_id in action_user_ids:
        try:
            ges.append(request_user_email(user_id, github_api_auth))
        except HTTPError as e:
            print(e)
            # Return email addresses that have received after exception happened
            return ges

    return ges


def get_email_from_events(rsp, name):
    """
    Parses out the email, if available from a user's public events
    """
    rsp = rsp.json()
    for event in rsp:
        payload = event.get('payload')
        if payload is not None:
            commits = payload.get('commits')
            if commits is not None:
                for commit in commits:
                    author = commit.get('author')
                    if author['name'] == name:
                        return author.get('email')

    return None


def request_user_email(user_id, github_api_auth):
    """
    Get email from the profile
    """
    rsp = get_operation(url=EndPoint.user_profile(user_id), github_api_auth=github_api_auth)

    # raise error when found nothing
    rsp.raise_for_status()

    rsp = rsp.json()
    ge = GithubUserEmail()
    ge.g_id = rsp['login']
    ge.name = rsp['name'].strip() if rsp['name'] else rsp['login']
    ge.email = rsp['email']
    ge.from_profile = True

    # Get user email from events
    if ge.email is None:
        rsp = get_operation(url=EndPoint.user_events(user_id), github_api_auth=github_api_auth)
        # raise error when found nothing
        rsp.raise_for_status()

        email = get_email_from_events(rsp, ge.name)
        if email is not None:
            ge.email = email
            ge.from_profile = False

    # Check if user opted out and respect that
    if user_has_opted_out(ge.email):
        ge.email = None

    return ge


def user_has_opted_out(email):
    """
    Checks if an email address was marked as opt-out
    """
    if email is not None:
        regex = compile('\\+[^@]*optout@g(?:oogle)?mail\\.com$', IGNORECASE)
        return regex.search(email) is not None
    else:
        return False


def format_email(ges):
    """
    John (john2) <John@example.org>; Peter James (pjames) <James@example.org>
    """
    formatted_email = []
    for ge in ges:
        if ge.email:
            try:
                formatted_email.append('{} ({}) <{}> [{}]'.format(ge.name.encode('utf8'), ge.g_id, ge.email, ge.from_profile))
            except UnicodeEncodeError:
                print(ge.g_id, ge.email, ge.from_profile)
                continue

    formatted_email = '\n'.join(formatted_email)
    return formatted_email


def api_status(github_api_auth):
    rsp = get(EndPoint.add_auth_info(EndPoint.rate_limit(), github_api_auth))
    rsp = rsp.json()
    status = GithubAPIStatus()
    status.core_reset_time = rsp['resources']['core']['reset']
    status.core_limit = rsp['resources']['core']['limit']
    status.core_remaining = rsp['resources']['core']['remaining']
    status.search_reset_time = rsp['resources']['search']['reset']
    status.search_limit = rsp['resources']['search']['limit']
    status.search_remaining = rsp['resources']['search']['remaining']
    return status


def repository(user_id, repo, github_api_auth):
    # Get information about repository
    rsp_repository = get_operation(url=EndPoint.repository(user_id=user_id, repo=repo), github_api_auth=github_api_auth)
    rsp_repository = rsp_repository.json()

    # Get information about contributors
    rsp_contributors = get_operation(url=EndPoint.contributors(user_id=user_id, repo=repo), github_api_auth=github_api_auth)
    rsp_contributors = rsp_contributors.json()

    repo_data = GithubRepository()
    repo_data.repo_id = rsp_repository['id']
    repo_data.name = rsp_repository['name']
    repo_data.description = rsp_repository['description']
    repo_data.stargazers_count = rsp_repository['stargazers_count']
    repo_data.watchers_count = rsp_repository['watchers_count']
    repo_data.forks_count = rsp_repository['forks_count']

    repo_data.contributors = [x['login'] for x in rsp_contributors]

    return repo_data


def get_operation(url, github_api_auth):
    headers = EndPoint.add_auth_info(github_api_auth)

    try:
        rsp = get(url=url, headers=headers)
    except Exception as e:
        print('The available request limit was exceeded for the Github API, waiting 1h until refresh it....')
        print(str(e))

        # Start to wait 1h
        for i in range(0, 20):
            print('      Process {}%'.format(i * 5))
            sleep(300)

        # Wait an extra minute
        sleep(60)

        # Repeat the last GitHub Operations to follow
        rsp = get(url)

    return rsp


if __name__ == '__main__':
    a = Catalogue()
    components = a.modules

    total_contributors = list()

    # Just for testing purposes
    # b = 1
    #
    # if b == 0:
    #     org = components['iot-agents/iotagent-lightweightM2M']['organization']
    #     repo = components['iot-agents/iotagent-lightweightM2M']['repository']
    #
    #     users = integrate_user_ids(user_id=org,
    #                                repo=repo,
    #                                actions=['contributor'],
    #                                github_api_auth=API_TOKEN)
    #
    #     exit(1)

    for repos in a.keys:
        print(f'Repo: {repos}')

        if repos != 'third-party/domibus':
            org = components[repos]['organization']
            repo = components[repos]['repository']

            # Actions: star, fork, watch, contributor
            users = integrate_user_ids(user_id=org,
                                       repo=repo,
                                       actions=['watch'],
                                       github_api_auth=API_TOKEN)

            total_contributors.append(list(users))
            print(f'Total number of contributors: {len(list(users))}')

    # Extract unique contributors
    total_contributors = list(set([item for row in total_contributors for item in row]))
    print(f'\nTotal number of contributors: {len(total_contributors)}')
