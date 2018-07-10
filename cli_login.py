#!/usr/bin/env python

import webbrowser
import configparser

from utils import start_local_server, is_remote_session

from globus_sdk import (NativeAppAuthClient, TransferClient,
                        AccessTokenAuthorizer)

import json
import os
import errno

configfile = os.path.expanduser('~/.globus-native-app/config')
configp = configparser.ConfigParser()
try:
    configp.read('configfile')
except:
    pass

config = {}

config['CLIENT_ID'] = '1b0dc9d3-0a2b-4000-8bd6-90fb6a79be86'
config['REDIRECT_URI'] = 'http://localhost:8000'
config['SCOPES'] = ('openid email profile '
          'urn:globus:auth:scope:transfer.api.globus.org:all')
config['SERVER_ADDRESS'] = ('127.0.0.1', 8000)

for i in ['CLIENT_ID', 'REDIRECT_URI', 'SCOPES', 'SERVER_ADDRESS']:
    try:
        config[i] = configp.get('Globus', i)
    except:
        pass

print(config)


def do_native_app_authentication(client_id, redirect_uri,
                                 requested_scopes=None):
    """
    Does a Native App authentication flow and returns a
    dict of tokens keyed by service name.
    """
    client = NativeAppAuthClient(client_id=client_id)
    client.oauth2_start_flow(requested_scopes=config['SCOPES'],
                             redirect_uri=redirect_uri)
    url = client.oauth2_get_authorize_url()

    server = start_local_server(listen=config['SERVER_ADDRESS'])

    if not is_remote_session():
        webbrowser.open(url, new=1)

    auth_code = server.wait_for_code()
    token_response = client.oauth2_exchange_code_for_tokens(auth_code)

    server.shutdown()

    # return a set of tokens, organized by resource server name
    return token_response.by_resource_server


def main():
    # start the Native App authentication process
    tokens = do_native_app_authentication(config['CLIENT_ID'], config['REDIRECT_URI'])

    transfer_token = tokens['transfer.api.globus.org']['access_token']

    # $HOME/.globus-native-app/<app UUID>/
    path = os.path.expanduser('~/.globus-native-app/'+config['CLIENT_ID'])

    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    with open(path+'/tokens.json', 'w') as outfile:
        json.dump(tokens, outfile)

    print('Successfully logged in: tokens are in %s' % path+'/tokens.json')


if __name__ == '__main__':
    if not is_remote_session():
        main()
    else:
        print('This example does not work on a remote session.')
