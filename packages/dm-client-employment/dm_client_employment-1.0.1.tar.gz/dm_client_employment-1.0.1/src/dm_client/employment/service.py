from django.conf import settings
from dm_core.meta.decorator import api_outbound_validator
from dm_core.meta.service import MetaClient
from dm_core.redis.utils import singleton
from dm_core.tracer.service import Requests, RequestAuthEnum
from requests.models import Response, Request
from .dataclasses import JobPostingDC


@singleton
class EmploymentClient(object):

    def __init__(self):
        meta_client = MetaClient()
        self.service = settings.SERVICE
        self.target_service = 'employment'
        self.url = meta_client.service_info(self.target_service, cache_key=self.target_service)['url']
        self.private_key = meta_client.my_service_info()['private_key']

    @api_outbound_validator()
    def _api(self, service, id, method, url_path, *args, **kwargs):
        response = Requests(service, id, self.private_key)(method, '{}{}'.format(self.url, url_path), *args, **kwargs)
        return response

    ############### Version ############################

    def version(self) -> (Response, Request):
        return self._api(self.target_service, 'version')

    ################## SCHEDULE ######################
    def schedule_internal_cleanup(self) -> (Response, Request):
        return self._api(self.target_service, 'schedule.internal.cleanup', request_auth=RequestAuthEnum.INTERNAL)

    ################# Core #############################

    def core_register(self, token, account_type_id: str=None, alias=None, name=None, mobile=None, email=None, address=None) -> (Response, Request):
        data = {
            'alias': alias,
            'profile': {
                'name': name,
                'mobile': mobile,
                'email': email,
                'address': address
            }
        }
        params = {}
        if account_type_id:
            params['account_type_id'] = account_type_id
        return self._api(self.target_service, 'core.register', json=data, params=params,
                         request_auth=RequestAuthEnum.EXTERNAL, auth=token)

    def core_list(self, token) -> (Response, Request):
        return self._api(self.target_service, 'core.list',
                         request_auth=RequestAuthEnum.EXTERNAL, auth=token)

    def core_set(self, token, account_id) -> (Response, Request):
        url_params = {'account_id': account_id}
        return self._api(self.target_service, 'core.set', url_params=url_params,
                         request_auth=RequestAuthEnum.EXTERNAL, auth=token)

    ####################### Personal ##############################

    def personal_profile_update(self, token: str, summary: str) -> (Response, Request):
        data = {
            'summary': summary
        }
        return self._api(self.target_service, 'personal.profile.update', request_auth=RequestAuthEnum.EXTERNAL,
                         auth=token, json=data)

    def personal_profile_get(self, token: str) -> (Response, Request):
        return self._api(self.target_service, 'personal.profile.get', request_auth=RequestAuthEnum.EXTERNAL, auth=token)

    def personal_profile_education_create(self, token: str, qualification, institution, started, finished, description) -> (Response, Request):
        data = {
            'qualification': qualification,
            'institution': institution,
            'started': started,
            'finished': finished,
            'description': description
        }
        return self._api(self.target_service, 'personal.profile.education.create', request_auth=RequestAuthEnum.EXTERNAL, auth=token, json=data)

    def personal_profile_career_create(self, token: str, job_title, company_name, started, ended, description) -> (Response, Request):
        data = {
            'job_title': job_title,
            'company_name': company_name,
            'started': started,
            'ended': ended,
            'description': description
        }
        return self._api(self.target_service, 'personal.profile.career.create', request_auth=RequestAuthEnum.EXTERNAL, auth=token, json=data)

    def personal_profile_resume_initiate(self, token: str) -> (Response, Request):
        return self._api(self.target_service, 'personal.profile.resume.initiate', request_auth=RequestAuthEnum.EXTERNAL, auth=token)

    def personal_profile_resume_complete(self, token: str, title: str, upload_id: str, expires_at: str) -> (Response, Request):
        data = {
            'upload_id': upload_id,
            'expires_at': expires_at,
            'title': title
        }
        return self._api(self.target_service, 'personal.profile.resume.complete', request_auth=RequestAuthEnum.EXTERNAL, auth=token, json=data)

    ####################### Business ##############################

    def business_profile_update(self, token: str, about: str, video_link: str) -> (Response, Request):
        data = {
            'about': about,
            'video_link': video_link
        }
        return self._api(self.target_service, 'business.profile.update', request_auth=RequestAuthEnum.EXTERNAL, auth=token, json=data)

    def business_profile_get(self, token: str) -> (Response, Request):
        return self._api(self.target_service, 'business.profile.get', request_auth=RequestAuthEnum.EXTERNAL, auth=token)

    def business_posting_create(self, token: str,  postingData: JobPostingDC) -> (Request, Response):
        return self._api(self.target_service, 'business.posting.create', json=postingData.to_dict(), request_auth=RequestAuthEnum.EXTERNAL, auth=token)

    def business_posting_update(self, token: str, post_id: str, postingData: JobPostingDC) -> (Request, Response):
        url_params = {
            'post_id': post_id
        }
        return self._api(self.target_service, 'business.posting.update', url_params=url_params, json=postingData.to_dict(), request_auth=RequestAuthEnum.EXTERNAL, auth=token)

    def business_posting_submit(self, token: str,  post_id: str, postingData: JobPostingDC) -> (Request, Response):
        url_params = {
            'post_id': post_id
        }
        return self._api(self.target_service, 'business.posting.submit', url_params=url_params, json=postingData.to_dict(), request_auth=RequestAuthEnum.EXTERNAL, auth=token)

    ####################### Jobs ##############################

    def jobs_category(self) -> (Response, Request):
        return self._api(self.target_service, 'jobs.category.get',  request_auth=RequestAuthEnum.ANONYMOUS)

    def jobs_sub_category(self, category_id: str) -> (Response, Request):
        url_params = {
            'category_id': category_id
        }
        return self._api(self.target_service, 'jobs.category.sub.get', url_params=url_params, request_auth=RequestAuthEnum.ANONYMOUS)

    def jobs_posting_meta(self) -> (Response, Request):
        return self._api(self.target_service, 'jobs.posting.meta', request_auth=RequestAuthEnum.ANONYMOUS)

    def jobs_detail(self, token: str, posting_id: str) -> (Response, Request):
        url_params = {
            'id': posting_id
        }
        return self._api(self.target_service, 'jobs.detail', url_params=url_params, request_auth=RequestAuthEnum.EXTERNAL, auth=token)

    def jobs_apply(self, token: str, posting_id: str, post_answers: list) -> (Response, Request):
        data = {
            'post': posting_id,
            'post_answers': post_answers
        }
        return self._api(self.target_service, 'jobs.apply', request_auth=RequestAuthEnum.EXTERNAL, auth=token, json=data)
    
    ####################### Support ###########################
    
    def support_review_post_patch(self, support_login: str, post_id: str, support_id: str, status: str, note: str = '') -> (Request, Response):
        data = {
            'note': note,
            'status': status,
            'support': support_id
        }
        url_params = {
            'post_id': post_id
        }
        return self._api(self.target_service, 'support.review.post.patch', url_params=url_params, json=data, request_auth=RequestAuthEnum.EXTERNAL, auth=support_login)

    def support_review_post_get(self, support_login: str, post_id: str, resource_id) -> (Request, Response):
        url_params = {
            'post_id': post_id
        }
        return self._api(self.target_service, 'support.review.post.get', url_params=url_params, request_auth=RequestAuthEnum.EXTERNAL, auth=support_login)