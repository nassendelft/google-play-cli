import httplib2
import time
from apiclient.discovery import build


class GooglePlayApi:

    def __init__(self, credentials, package_name):
        http = httplib2.Http()
        http = credentials.authorize(http)
        self.edit = None
        self.package_name = package_name
        self.service = build('androidpublisher', 'v2', http=http)

    def start_edit(self):
        return Edit(self.service, self.package_name)

    def entitlements(self):
        return self.service.entitlements().list(packageName=self.package_name).execute()

    def reviews(self, review_id):
        if review_id is None:
            return self.service.reviews().list(packageName=self.package_name).execute()
        else:
            return self.service.reviews().list(packageName=self.package_name, reviewId=review_id).execute()

    def reviews_reply(self, review_id, reply):
        result = self.service.reviews().reply(
                packageName=self.package_name, reviewId=review_id, body={u'replyText': reply}
        ).execute()

        


class Edit:

    def __init__(self, service, package_name):
        self.package_name = package_name
        self.service = service
        self.edit = service.edits().insert(body={}, packageName=self.package_name).execute()
        self.edit['created'] = time.time()

    def commit(self):
        if self.edit is None:
            print 'Nothing to commit'

        result = self.service.edits().commit(editId=self.edit['id'], packageName=self.package_name).execute()

        self.edit = None

        return result

    def increase_rollout(self, rollout_fraction, track='production', version_code=None):
        """
        Set the roll out fraction to given package name. If no version_codes is given it
        uses the highest version code only.
        :param track: either 'production', 'beta' or 'alpha'
        :param rollout_fraction: in range of 0.1 to 1
        :param version_code: the version codes to update or None to use the latest version
        """

        if self.edit is None:
            raise IllegalState('call start_edit() before using this method')

        edit_id = self.edit['id']

        if version_code is None:

            track_version_code = self.get_active_version_code(track)

            if track_version_code is None:
                raise ValueError('There are is no version available')

            version_code = track_version_code

        print 'Changing version %d to %.2f' % (version_code, rollout_fraction)

        track_response = self.service.edits().tracks().update(
                editId=edit_id,
                track=track,
                packageName=self.package_name,
                body={u'track': track,
                      u'userFraction': rollout_fraction,
                      u'versionCodes': [version_code]}
        ).execute()

        print 'Track %s is set for version code(s) %s' % (
            track_response['track'], str(track_response['versionCodes']))

    def get_active_version_code(self, track="production"):

        if self.edit is None:
            raise IllegalState('call start_edit() before using this method')

        track_result = self.service.edits().tracks().get(
                editId=self.edit['id'], packageName=self.package_name, track=track
        ).execute()

        version_codes = track_result['versionCodes']

        if version_codes is None or len(version_codes) == 0:
            return None

        return version_codes[-1]


class IllegalState(Exception):
    pass
