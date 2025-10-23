from django.conf import settings
from dm_core.meta.service import MetaClient
from dm_core.meta.decorator import api_outbound_validator
from dm_core.redis.utils import singleton
from dm_core.tracer.service import Requests, RequestAuthEnum
from requests.models import Response, Request


@singleton
class AuthClient(object):

    def __init__(self):
        meta_client = MetaClient()
        self.service = settings.SERVICE
        self.target_service = 'auth'
        self.url = meta_client.service_info(self.target_service, cache_key=self.target_service)['url']
        self.private_key = meta_client.my_service_info()['private_key']

    @api_outbound_validator()
    def _api(self, service, api_id, method, url_path, *args, **kwargs):
        response, request = Requests(service, api_id, self.private_key)(method, '{}{}'.format(self.url, url_path), *args, **kwargs)
        return response, request

    #################### Version ########################

    def version(self) -> (Response, Request):
        return self._api(self.target_service, 'version')

    ###################### APP ##########################

    def app_internal_service(self, service_name: str) -> (Response, Request):
        """
        Internal Service: Get Service information for the AUTH app
        """
        params = {
            'name': service_name
        }
        return self._api(self.target_service, 'app.internal.service', request_auth=RequestAuthEnum.INTERNAL, params=params)

    def app_service(self, service_url: str) -> (Response, Request):
        """
        get_service

        note: service is the attribute of the class storing the "service" name
        """
        params = {
            'service': service_url
        }
        return self._api(self.target_service, 'app.service', params=params)

    ################### Authz ##########################

    def authz_permissions(self):
        return self._api(self.target_service, 'authz.permissions')

    ##################### CORE #########################

    def core_captcha(self) -> (Response, Request):
        """
        Generate captcha: Generates captcha
        """
        return self._api(self.target_service, 'core.captcha')


    def core_internal_captcha(self) -> (Response, Request):
        """
        Internal Captcha: Generate captcha and code

        - For internal testing only, requires internal auth and permitted to tester only
        """
        return self._api(self.target_service, 'core.internal.captcha',  request_auth=RequestAuthEnum.INTERNAL)

    def core_security_questions(self) -> (Response, Request):
        """
        Security questions: Get list of security questions
        """
        return self._api(self.target_service, 'core.security-questions')

    ################## SCHEDULE ######################
    def schedule_internal_cleanup(self) -> (Response, Request):
        return self._api(self.target_service, 'schedule.internal.cleanup', request_auth=RequestAuthEnum.INTERNAL)

    ################ USERS APP #######################

    def user_exists_email(self, email: str) -> (Response, Request):
        data = {
            'email': email
        }
        return self._api(self.target_service, 'user.exists-email', json=data)

    def user_exists_mobile(self, mobile: str) -> (Response, Request):
        data = {
            'mobile': mobile
        }
        return self._api(self.target_service, 'user.exists-mobile', json=data)

    def user_profile_get(self, auth) -> (Response, Request):
        return self._api(self.target_service, 'user.profile.get', request_auth=RequestAuthEnum.EXTERNAL, auth=auth)

    def user_internal_profile(self, user_id) -> (Response, Request):
        params = {
            'user_id': user_id
        }
        return self._api(self.target_service, 'user.internal.profile.get', request_auth=RequestAuthEnum.INTERNAL, params=params)

    def user_register_complete(self, language: str, timezone: str, registration_token: str) -> (Response, Request):
        data = {
            'language': language,
            'timezone': timezone
        }
        url_params = {
            'token': registration_token
        }
        return self._api(self.target_service, 'user.register-complete', json=data, url_params=url_params)

    def user_register_initiate(self, name: str, email: str, mobile: str, challenge: str, response: str, *args, **kwargs) -> (Response, Request):
        data = {
            'register': {
                'name': name,
                'email': email,
                'mobile': mobile
            },
            'captcha': {
                'challenge': challenge,
                'response': response
            }
        }
        return self._api(self.target_service, 'user.register-initiate', json=data)

    def user_register_reverify(self, token) -> (Response, Request):
        return self._api(self.target_service, 'user.register-reverify')

    def user_register_security(self, registration_token: str, password: str, mobile_secret: str, email_secret: str, *args, **kwargs) -> (Response, Request):
        data = {
            'validate': {
                'mobile_secret': mobile_secret,
                'email_secret': email_secret,
            },
            'password': password
        }
        url_params = {
            'token': registration_token
        }
        return  self._api(self.target_service, 'user.register-security', json=data, url_params=url_params)

    def user_register_security_recovery(self, registration_token: str, security: list, *args, **kwargs) -> (Response, Request):
        data = {
            'security': security,
        }
        url_params = {
            'token': registration_token
        }
        return self._api(self.target_service, 'user.register-security-recovery', json=data, url_params=url_params)

    def user_register_complete(self, registration_token: str, language: str, timezone: str, *args, **kwargs) -> (Response, Request):
        data = {
            'language': language,
            'timezone': timezone
        }
        url_params = {
            'token': registration_token
        }
        return self._api(self.target_service, 'user.register-complete', json=data, url_params=url_params)

    def user_password_change(self, token: str, current_password: str, new_password: str, *args, **kwargs) -> (Response, Request):
        data = {
            'current_password': current_password,
            'new_password': new_password
        }
        return self._api(self.target_service, 'user.password-change', json=data, request_auth=RequestAuthEnum.EXTERNAL, auth=token)

    def user_profile_patch(self, token: str, key: str, value: str|dict, *args, **kwargs) -> (Response, Request):
        data = {}
        if key in ['address', 'date_of_birth', 'language', 'timezone', 'avatar']:
            data['profile'] = {key: value}
        else:
            data[key] = value
        return self._api(self.target_service, 'user.profile.patch', json=data, request_auth=RequestAuthEnum.EXTERNAL, auth=token)

    def user_profile_avatar_initiate(self, token: str):
        return self._api(self.target_service, 'user.profile-avatar-initiate', request_auth=RequestAuthEnum.EXTERNAL, auth=token)


    ##################### CAS #######################

    def sso_cas_login_credential_requestor(self, service=None, dm_castgt=None, **kwargs) -> (Response, Request):
        headers = {}
        params = {}
        if service is not None:
            params['service'] = service
        if dm_castgt is not None:
            headers['DM-CASTGT'] = f"Bearer {dm_castgt}"
        return self._api(self.target_service, 'sso.cas.login-credential-requestor', params=params, headers=headers, **kwargs)

    def sso_cas_login_credential_acceptor(self, data: dict, params: dict, **kwargs) -> (Response, Request):
        return self._api(self.target_service, 'sso.cas.login-credential-acceptor', json=data, params=params, **kwargs)

    def sso_cas_logout(self, auth: str) -> (Response, Request):
        return self._api(self.target_service, 'sso.cas.logout', request_auth=RequestAuthEnum.EXTERNAL, auth=auth)

    def sso_cas_service_validate(self, ticket, service):
        """
        Perform service validation of a ticket
        """
        params = {
            'ticket': ticket,
            'service': service
        }
        return self._api(self.target_service, 'sso.cas.service-validate', params=params, request_auth=RequestAuthEnum.INTERNAL)

