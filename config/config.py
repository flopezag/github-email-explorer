#!/usr/bin/env python
# -*- encoding: utf-8 -*-
##
# Copyright 2021 FIWARE Foundation, e.V.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
##

from os.path import dirname, join, abspath
from yaml import load, Loader, YAMLError

__author__ = 'Fernando López'

__version__ = '1.0.0'

name = 'github-email-explorer'

policySetVersion = str()

CODE_HOME = dirname(dirname(abspath(__file__)))
CONFIG_HOME = join(CODE_HOME, 'config')
CONFIG_FILE = join(CONFIG_HOME, 'config.yaml')

API_TOKEN = None
with open(CONFIG_FILE, 'r') as stream:
    try:
        API_TOKEN = load(stream, Loader=Loader)
        API_TOKEN = API_TOKEN['github_api_auth']
        if API_TOKEN == '<GitHub API Token>':
            print('ERROR, Authenticating with GitHub API. Need to provide a GitHub API Token in the config.yaml file.')
            exit(1)
    except YAMLError as exc:
        print(exc)
