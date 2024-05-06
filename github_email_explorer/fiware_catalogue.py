from requests import get
from time import sleep
from github_email_explorer.api_url import GitHubEndPoint as EndPoint
from config.config import API_TOKEN


class Catalogue(object):
    def __init__(self):
        self.url = 'https://raw.githubusercontent.com/FIWARE/catalogue/master/.gitmodules'
        self.github_api_auth = API_TOKEN
        self.modules = dict()
        self.keys = list()

        self.content = self.get_operation(url=self.url, github_api_auth=self.github_api_auth)
        self.content = self.content.text
        self.parse_gitmodules()

        self.keys = list(self.modules.keys())

    def parse_gitmodules(self):
        current_module = None

        for line in self.content.split('\n'):  # .splitlines():
            line = line.strip()

            if line.startswith('[submodule'):
                current_module = line.split('"')[1]
                self.modules[current_module] = {}
            elif line.startswith('path'):
                path = line.split('=')[1].strip()
                self.modules[current_module]['path'] = path
            elif line.startswith('url'):
                url = line.split('=')[1].strip()
                self.modules[current_module]['url'] = url

                organization, repository = self.extract_data(url)
                self.modules[current_module]['organization'] = organization
                self.modules[current_module]['repository'] = repository

    @staticmethod
    def extract_data(url) -> [str, str]:
        data = url.split("/")[3:]

        organization = data[0]

        last_dot_index = data[1].rfind(".")

        if last_dot_index != -1:
            repository = data[1][:last_dot_index]
        else:
            repository = data[1]

        return organization, repository

    def get_operation(self, url, github_api_auth):
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
    substring = str()

    string = 'lightweightm2m-iotagent'

    last_dot_index = string.rfind(".")

    if last_dot_index != -1:
        substring = string[:last_dot_index]

    print(substring)
