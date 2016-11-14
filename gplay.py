#!/usr/bin/python
"""Interact with Google Play services
Usage:
  gplay.py track active
    (--service-p12=FILE | --service-json=FILE | --oauth-json=FILE | (--oauth --client-id=ID --client-secret=SECRET))
    [--track=TRACK] PACKAGE_NAME
  gplay.py rollout
    (--service-p12=FILE | --service-json=FILE | --oauth-json=FILE | (--oauth --client-id=ID --client-secret=SECRET))
    [--track=TRACK] [--version-code=CODE] PACKAGE_NAME FRACTION

Options:
  --service-p12=FILE       uses a p12 file for service account credentials
  --service-json=FILE      uses a json file for service account credentials
  --oauth-json=FILE        uses a client-secret json file for oauth credentials (opens browser)
  --oauth                  uses a client-secret supplied with --client-id and --client-secret (opens browser)
  --client-id=ID
  --client-secret=SECRET

  --track=TRACK            select track (production, beta or alpha)  [default: production]
  --version-code=CODE           app version code to select [default: latest]
"""
from docopt import docopt
from oauth2client import tools
from oauth2client.client import flow_from_clientsecrets, OAuth2WebServerFlow, Storage
from oauth2client.service_account import ServiceAccountCredentials
from google_play_api import GooglePlayApi

if __name__ == '__main__':

    args = docopt(__doc__, version='1.0.0')

    credentials = None
    flow = None

    scope = 'https://www.googleapis.com/auth/androidpublisher'
    redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
    if args['--service-json'] is not None:
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
                args['--service-json'],
                [scope])
    if args['--service-p12'] is not None:
        credentials = ServiceAccountCredentials.from_p12_keyfile(
                args['--service-p12'],
                [scope])
    if args['--oauth-json'] is not None:
        flow = flow_from_clientsecrets(
                args['--oauth-json'],
                scope=scope,
                redirect_uri=redirect_uri)
    if args['--oauth'] is True:
        flow = OAuth2WebServerFlow(
                client_id=args['--client-id'],
                client_secret=args['--client-secret'],
                scope=scope,
                redirect_uri=redirect_uri)

    if flow is not None:
        storage = Storage('credentials.dat')
        credentials = storage.get()
        if credentials is None or credentials.invalid:
            credentials = tools.run_flow(flow, storage)

    if credentials is None:
        exit(ValueError('missing credentials'))

    api = GooglePlayApi(credentials, args['PACKAGE_NAME'])

    if args['track'] is True:
        if args['active'] is True:
            edit = api.start_edit()
            print edit.get_active_version_code('production')

    if args['rollout'] is True:
        edit = api.start_edit()
        rollout_fraction = float(args['FRACTION'])
        version_code = args['--version-code'] if not 'latest' else None
        track = args['--track'] if not False else 'production'
        edit.increase_rollout(rollout_fraction, track, version_code)
        commit_result = edit.commit_edit()
        print '(%s) Successfully rolled out to %.2f' % (commit_result['id'], rollout_fraction)
