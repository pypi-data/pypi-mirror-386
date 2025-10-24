from requests import Session
from .define_api import *
from .log_ import logger
from .utils import random_cookies, encode_base64
from typing import Optional, Union, Iterator
from .parse_api import paser_node_posts_group, paser_node_posts_page, paser_node_post, parse_node_comments, parse_node_reply
import time



class FaceApiWrapper:
    @staticmethod
    def get_node_posts_group(group_id: Union[str, int], session: Optional[Session] = None , **kwargs):
        count_post = 0
        cursor = ""
        timeout = kwargs.pop('timeout', DEFAULT_REQUESTS_TIMEOUT)
        sleep_time = kwargs.pop('sleep_time', DEFAULT_SLEEP_TIME)
        post_limit = kwargs.pop('post_limit', 1000)
        cookies = kwargs.pop('cookies', None)
        while cursor is not None:
            try:
                if cookies:
                    pass
                else:
                    if RANDOM_COOKIE:
                        cookies = {
                            'wd': '1912x958',
                            'datr': random_cookies(32),
                        }
                if cursor == "":
                    data = {
                        'fb_api_caller_class': 'RelayModern',
                        'fb_api_req_friendly_name': 'GroupsCometFeedRegularStoriesPaginationQuery',
                        'variables': '{"count":3,"cursor":null,"feedLocation":"GROUP","feedType":"DISCUSSION","feedbackSource":0,"focusCommentID":null,"privacySelectorRenderLocation":"COMET_STREAM","renderLocation":"group","scale":1,"sortingSetting":"CHRONOLOGICAL","stream_initial_count":1,"useDefaultActor":false,"id":"' + str(group_id) + '","__relay_internal__pv__IsWorkUserrelayprovider":false,"__relay_internal__pv__IsMergQAPollsrelayprovider":false,"__relay_internal__pv__CometUFIReactionsEnableShortNamerelayprovider":false,"__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider":true,"__relay_internal__pv__StoriesTrayShouldShowMetadatarelayprovider":false,"__relay_internal__pv__StoriesRingrelayprovider":false}',
                        'server_timestamps': 'true',
                        'doc_id': '24843655751947608',
                    }
                else:
                    data = {
                        'fb_api_caller_class': 'RelayModern',
                        'fb_api_req_friendly_name': 'GroupsCometFeedRegularStoriesPaginationQuery',
                        'variables': '{"count":3,"cursor":"' + cursor + '","feedLocation":"GROUP","feedType":"DISCUSSION","feedbackSource":0,"focusCommentID":null,"privacySelectorRenderLocation":"COMET_STREAM","renderLocation":"group","scale":1,"sortingSetting":"CHRONOLOGICAL","stream_initial_count":1,"useDefaultActor":false,"id":"' + str(group_id) + '","__relay_internal__pv__IsWorkUserrelayprovider":false,"__relay_internal__pv__IsMergQAPollsrelayprovider":false,"__relay_internal__pv__CometUFIReactionsEnableShortNamerelayprovider":false,"__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider":true,"__relay_internal__pv__StoriesTrayShouldShowMetadatarelayprovider":false,"__relay_internal__pv__StoriesRingrelayprovider":false}',
                        'server_timestamps': 'true',
                        'doc_id': '24843655751947608',
                    }
                if session:
                    if cookies:
                        response = session.post(API_URL, data=data, cookies=cookies, timeout=timeout)
                    else:
                        response = session.post(API_URL, data=data, timeout=timeout)
                else:
                    logger.warning(f"Warning >> session is None ")
                    break
                if response:
                    #print(response.text)
                    res = paser_node_posts_group(response.text)
                    cursor = res['cursor']
                    count_post += len(res['node_posts'])
                    yield res['node_posts']
                    if post_limit != -1:
                        if count_post >= post_limit:
                            logger.info(f"Get sussces {count_post} post")
                            break
                    time.sleep(sleep_time)
                else:
                    break
            except Exception as e:
                logger.error(f"Error func get_node_posts_group: {e}")
                break
    @staticmethod
    def get_node_posts_page(page_id: Union[str, int], session: Optional[Session] = None , **kwargs):
        count_post = 0
        cursor = ""
        timeout = kwargs.pop('timeout', DEFAULT_REQUESTS_TIMEOUT)
        sleep_time = kwargs.pop('sleep_time', DEFAULT_SLEEP_TIME)
        post_limit = kwargs.pop('post_limit', 1000)
        cookies = kwargs.pop('cookies', None)
        max_retry = kwargs.pop('max_retry', 3)
        retry = 0
        while cursor is not None:
            try:
                if cookies:
                    pass
                else:
                    if RANDOM_COOKIE:
                        cookies = {
                            'wd': '1912x958',
                            'datr': random_cookies(32),
                        }
                if cursor == "":
                    data = {
                        'av': '',
                        '__user': '',
                        '__a': '1',
                        '__comet_req': '15',
                        'fb_dtsg': 'NAcMm4E0lcQC8DNeO4otqK6dkDMADS0jRFpnJTxpy6rk7DjpH6SYjaA:2:1710219296', # Anti-CSRF Token của Facebook – dùng để chặn hình thức tấn công CSRF
                        'jazoest': '25328',
                        'lsd': 'BsQuJc5kRmhQebv0VOsHcH',
                        'fb_api_caller_class': 'RelayModern',
                        'fb_api_req_friendly_name': 'ProfileCometTimelineFeedRefetchQuery',
                        'variables': '{"afterTime":null,"beforeTime":null,"count":3,"cursor":null,"feedLocation":"TIMELINE","feedbackSource":0,"focusCommentID":null,"memorializedSplitTimeFilter":null,"omitPinnedPost":true,"postedBy":{"group":"OWNER"},"privacy":null,"privacySelectorRenderLocation":"COMET_STREAM","renderLocation":"timeline","scale":1,"stream_count":1,"taggedInOnly":null,"useDefaultActor":false,"id":"' + str(page_id) + '","__relay_internal__pv__IsWorkUserrelayprovider":false,"__relay_internal__pv__IsMergQAPollsrelayprovider":false,"__relay_internal__pv__CometUFIReactionsEnableShortNamerelayprovider":false,"__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider":true,"__relay_internal__pv__StoriesTrayShouldShowMetadatarelayprovider":false,"__relay_internal__pv__StoriesRingrelayprovider":false}',
                        'server_timestamps': 'true',
                        'doc_id': '7187264744661668',
                    }
                else:
                    data = {
                        'av': '',
                        '__user': '',
                        '__a': '1',
                        '__comet_req': '15',
                        'fb_dtsg': 'NAcMm4E0lcQC8DNeO4otqK6dkDMADS0jRFpnJTxpy6rk7DjpH6SYjaA:2:1710219296', # Anti-CSRF Token của Facebook – dùng để chặn hình thức tấn công CSRF
                        'jazoest': '25328',
                        'lsd': 'BsQuJc5kRmhQebv0VOsHcH',
                        'fb_api_caller_class': 'RelayModern',
                        'fb_api_req_friendly_name': 'ProfileCometTimelineFeedRefetchQuery',
                        'variables': '{"afterTime":null,"beforeTime":null,"count":3,"cursor":"' + cursor +'","feedLocation":"TIMELINE","feedbackSource":0,"focusCommentID":null,"memorializedSplitTimeFilter":null,"omitPinnedPost":true,"postedBy":{"group":"OWNER"},"privacy":null,"privacySelectorRenderLocation":"COMET_STREAM","renderLocation":"timeline","scale":1,"stream_count":1,"taggedInOnly":null,"useDefaultActor":false,"id":"'+ str(page_id) +'","__relay_internal__pv__IsWorkUserrelayprovider":false,"__relay_internal__pv__IsMergQAPollsrelayprovider":false,"__relay_internal__pv__CometUFIReactionsEnableShortNamerelayprovider":false,"__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider":true,"__relay_internal__pv__StoriesTrayShouldShowMetadatarelayprovider":false,"__relay_internal__pv__StoriesRingrelayprovider":false}',
                        'server_timestamps': 'true',
                        'doc_id': '7187264744661668',
                    }
                if session:
                    if cookies:
                        response = session.post(API_URL, data=data, cookies=cookies, timeout=timeout)
                    else:
                        response = session.post(API_URL, data=data, timeout=timeout)
                else:
                    logger.warning(f"Warning >> session is None ")
                    break
                if response:
                    res = paser_node_posts_page(response.text)
                    cursor = res['cursor']
                    count_post += len(res['node_posts'])
                    yield res['node_posts']
                    if post_limit != -1:
                        if count_post >= post_limit:
                            logger.info(f"Get sussces {count_post} post")
                            break
                    time.sleep(sleep_time)
                    retry = 0
                else:
                    break
            except Exception as e:
                logger.error(f"Error func get_node_posts_page: {e}")
                if retry < max_retry:
                    retry += 1
                    logger.info(f"Retry {retry}/{max_retry}")
                    logger.info(f"Retry with cursor: {cursor}")
                    time.sleep(sleep_time)
                    continue
                else:
                    logger.error(f"Max retry {max_retry} reached. Stop.")
                    break


    @staticmethod
    def get_node_post_group(groupID: Union[str, int], uid: Union[str, int, None] = None, post_id: Union[str, int, None] = None, storyID: Optional[str] = None, session: Optional[Session] = None , **kwargs):
        try:
            timeout = kwargs.pop('timeout', DEFAULT_REQUESTS_TIMEOUT)
            cookies = kwargs.pop('cookies', None)
            if cookies:
                    pass
            else:
                if RANDOM_COOKIE:
                    cookies = {
                        'wd': '1912x958',
                        'datr': random_cookies(32),
                    }
            if not storyID:
                if post_id and uid:
                    storyID = encode_base64(f"S:_I{uid}:VK:{post_id}")
                else:
                    raise ValueError("You need to specify either storyID or post_id and uid")
            if storyID and groupID:
                data = {
                    'av': '',
                    '__user': '',
                    '__a': '1',
                    '__comet_req': '15',
                    'fb_dtsg': 'NAcOyerE6mxRWxDB2tec0dwDeC28OzTNsiwM6EeTGIDCrR6HOj98ymg:2:1710219296',
                    'jazoest': '25410',
                    'lsd': 'BwgDP_dgC_fNpBzBh2kK8f',
                    'qpl_active_flow_ids': '431626709',
                    'fb_api_caller_class': 'RelayModern',
                    'fb_api_req_friendly_name': 'CometGroupPermalinkRootContentFeedQuery',
                    'variables': '{"feedbackSource":2,"feedLocation":"DEDICATED_COMMENTING_SURFACE","focusCommentID":null,"groupID":"' + str(groupID) + '","privacySelectorRenderLocation":"COMET_STREAM","renderLocation":"group_permalink","scale":1,"storyID":"' + storyID + '","useDefaultActor":false,"__relay_internal__pv__GroupsCometGroupChatLazyLoadLastMessageSnippetrelayprovider":false,"__relay_internal__pv__IsWorkUserrelayprovider":false,"__relay_internal__pv__IsMergQAPollsrelayprovider":false,"__relay_internal__pv__CometUFIReactionsEnableShortNamerelayprovider":false,"__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider":true,"__relay_internal__pv__StoriesTrayShouldShowMetadatarelayprovider":false,"__relay_internal__pv__StoriesRingrelayprovider":false}', 
                    'server_timestamps': 'true',
                    'doc_id': '7427501437309006',
                }
                if session:
                    if cookies:
                        response = session.post(API_URL, data=data, cookies=cookies, timeout=timeout)
                    else:
                        response = session.post(API_URL, data=data, timeout=timeout)
                else:
                    raise ValueError("Session is None")
                # response = requests.post(API_URL, headers=HEADERS, data=data)
                res = paser_node_post(response.text)
                return res
            else:
                raise ValueError("You need to specify either storyID and groupID")
        except Exception as e:
            logger.error(f"ERROR >> {e}")
            return {}
    @staticmethod
    def get_node_post_page(uid: Union[str, int, None] = None, post_id: Union[str, int, None] = None, storyID: Optional[str] = None, session: Optional[Session] = None , **kwargs):
        try:
            timeout = kwargs.pop('timeout', DEFAULT_REQUESTS_TIMEOUT)
            cookies = kwargs.pop('cookies', None)
            if cookies:
                    pass
            else:
                if RANDOM_COOKIE:
                    cookies = {
                        'wd': '1912x958',
                        'datr': random_cookies(32),
                    }
            if not storyID:
                if post_id and uid:
                    storyID = encode_base64(f"S:_I{uid}:{post_id}:{post_id}")
                else:
                    raise ValueError("You need to specify either storyID or post_id and uid")
            if storyID:
                data = {
                    'av': '',
                    '__user': '',
                    '__a': '1',
                    '__comet_req': '15',
                    'fb_dtsg': 'NAcMm4E0lcQC8DNeO4otqK6dkDMADS0jRFpnJTxpy6rk7DjpH6SYjaA:2:1710219296',
                    'jazoest': '25328',
                    'lsd': 'BsQuJc5kRmhQebv0VOsHcH',
                    'fb_api_caller_class': 'RelayModern',
                    'fb_api_req_friendly_name': 'CometSinglePostContentQuery',
                    'variables': '{"feedbackSource":2,"feedLocation":"PERMALINK","focusCommentID":null,"privacySelectorRenderLocation":"COMET_STREAM","renderLocation":"permalink","scale":1,"storyID":"' + storyID + '","useDefaultActor":false,"__relay_internal__pv__IsWorkUserrelayprovider":false,"__relay_internal__pv__IsMergQAPollsrelayprovider":false,"__relay_internal__pv__CometUFIReactionsEnableShortNamerelayprovider":false,"__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider":true,"__relay_internal__pv__StoriesTrayShouldShowMetadatarelayprovider":false,"__relay_internal__pv__StoriesRingrelayprovider":false}',
                    'server_timestamps': 'true',
                    'doc_id': '6429441107159285',
                }
                if session:
                    if cookies:
                        response = session.post(API_URL, data=data, cookies=cookies, timeout=timeout)
                    else:
                        response = session.post(API_URL, data=data, timeout=timeout)
                else:
                    raise ValueError("Session is None")
                # response = requests.post(API_URL, headers=HEADERS, data=data)
                res = paser_node_post(response.text)
                return res
            else:
                raise ValueError("You need to specify either storyID")
        except Exception as e:
            logger.error(f"ERROR >> {e}")
            return {}
    @staticmethod
    def get_all_comment_post_permalink(postID: Union[str, int], session: Optional[Session] = None , **kwargs):
        try:
            timeout = kwargs.pop('timeout', DEFAULT_REQUESTS_TIMEOUT)
            cookies = kwargs.pop('cookies', None)
            if cookies:
                    pass
            else:
                if RANDOM_COOKIE:
                    cookies = {
                        'wd': '1912x958',
                        'datr': random_cookies(32),
                    }
            id_feedback = encode_base64(f"feedback:{postID}")
            data = {
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'CommentListComponentsRootQuery',
                'variables': '{"commentsIntentToken":"RANKED_UNFILTERED_CHRONOLOGICAL_REPLIES_INTENT_V1","feedLocation":"PERMALINK","feedbackSource":2,"focusCommentID":null,"scale":1,"useDefaultActor":false,"id":"' + id_feedback+ '","__relay_internal__pv__VideoPlayerRelayReplaceDashManifestWithPlaylistrelayprovider":false}',
                'server_timestamps': 'true',
                'doc_id': '7563509803699896',
            }
            if session:
                if cookies:
                    response = session.post(API_URL, data=data, cookies=cookies, timeout=timeout)
                else:
                    response = session.post(API_URL, data=data, timeout=timeout)
            else:
                raise ValueError("Session is None")
            return parse_node_comments(response.text)
        except Exception as e:
            logger.error(f"Error func get_all_comment_post_permalink: {e}")
            return []
    @staticmethod
    def get_all_comment_post_dcs(postID: Union[str, int], session: Optional[Session] = None , **kwargs): #DEDICATED_COMMENTING_SURFACE
        try:
            timeout = kwargs.pop('timeout', DEFAULT_REQUESTS_TIMEOUT)
            cookies = kwargs.pop('cookies', None)
            if cookies:
                    pass
            else:
                if RANDOM_COOKIE:
                    cookies = {
                        'wd': '1912x958',
                        'datr': random_cookies(32),
                    }
            id_feedback = encode_base64(f"feedback:{postID}")
            data = {
                'qpl_active_flow_ids': '431626709',
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'CommentListComponentsRootQuery',
                'variables': '{"commentsIntentToken":"CHRONOLOGICAL_UNFILTERED_INTENT_V1","feedLocation":"DEDICATED_COMMENTING_SURFACE","feedbackSource":110,"focusCommentID":null,"scale":1,"useDefaultActor":false,"id":"' + id_feedback+ '"}',
                'server_timestamps': 'true',
                'doc_id': '7563509803699896',
            }
            if session:
                if cookies:
                    response = session.post(API_URL, data=data, cookies=cookies, timeout=timeout)
                else:
                    response = session.post(API_URL, data=data, timeout=timeout)
            else:
                raise ValueError("Session is None")
            return parse_node_comments(response.text)
        except Exception as e:
            logger.error(f"Error func get_all_comment_post_permalink: {e}")
            return []
            
    @staticmethod
    def get_reply_depth1_comment(expansionToken: Optional[str], id_comment: Optional[str] = "", feedback_id: Optional[str] = "", session: Optional[Session] = None, **kwargs):
        try:
            #Nếu lấy reply trên group thì feedLocation="DEDICATED_COMMENTING_SURFACE" sẽ lấy được nhiều hơn
            #Còn lấy trên page thì feedLocation="PERMALINK" 
            timeout = kwargs.pop('timeout', DEFAULT_REQUESTS_TIMEOUT)
            cookies = kwargs.pop('cookies', None)
            feedLocation = kwargs.pop('feedLocation', 'DEDICATED_COMMENTING_SURFACE')
            if cookies:
                    pass
            else:
                if RANDOM_COOKIE:
                    cookies = {
                        'wd': '1912x958',
                        'datr': random_cookies(32),
                    }
            if not feedback_id:
                if id_comment:
                    feedback_id = encode_base64(f"feedback:{id_comment}")
                else:
                    raise  ValueError("You need to specify either feedback_id or id_comment")

            data = {
                'qpl_active_flow_ids': '431626709',
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'Depth1CommentsListPaginationQuery',
                'variables': '{"clientKey":null,"expansionToken":"' + expansionToken + '","feedLocation":"' + feedLocation + '","focusCommentID":null,"repliesAfterCount":null,"repliesAfterCursor":null,"repliesBeforeCount":null,"repliesBeforeCursor":null,"scale":1,"useDefaultActor":false,"id":"' + feedback_id + '","__relay_internal__pv__VideoPlayerRelayReplaceDashManifestWithPlaylistrelayprovider":false}',
                'server_timestamps': 'true',
                'doc_id': '7519949104723463',
            }
            if session:
                if cookies:
                    response = session.post(API_URL, data=data, cookies=cookies, timeout=timeout)
                else:
                    response = session.post(API_URL, data=data, timeout=timeout)
            else:
                raise ValueError("Session is None")
            
            return parse_node_reply(response.text)
        except Exception as e:
            logger.error(f"Error func get_reply_depth1_comment: {e}")
            return []
    @staticmethod
    def get_reply_depth2_comment(expansionToken: Optional[str], id_comment: Optional[str] = "", feedback_id: Optional[str] = "", session: Optional[Session] = None, **kwargs):
        try:
            #Nếu lấy reply trên group thì feedLocation="DEDICATED_COMMENTING_SURFACE" sẽ lấy được nhiều hơn
            #Còn lấy trên page thì feedLocation="PERMALINK" 
            timeout = kwargs.pop('timeout', DEFAULT_REQUESTS_TIMEOUT)
            cookies = kwargs.pop('cookies', None)
            feedLocation = kwargs.pop('feedLocation', 'DEDICATED_COMMENTING_SURFACE')
            if cookies:
                    pass
            else:
                if RANDOM_COOKIE:
                    cookies = {
                        'wd': '1912x958',
                        'datr': random_cookies(32),
                    }
            if not feedback_id:
                if id_comment:
                    feedback_id = encode_base64(f"feedback:{id_comment}")
                else:
                    raise  ValueError("You need to specify either feedback_id or id_comment")

            data = {
                'qpl_active_flow_ids': '431626709',
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'Depth2CommentsListPaginationQuery',
                'variables': '{"clientKey":null,"expansionToken":"' + expansionToken + '","feedLocation":"' + feedLocation + '","scale":1,"subRepliesAfterCount":null,"subRepliesAfterCursor":null,"subRepliesBeforeCount":null,"subRepliesBeforeCursor":null,"useDefaultActor":false,"id":"' + feedback_id + '","__relay_internal__pv__VideoPlayerRelayReplaceDashManifestWithPlaylistrelayprovider":false}',
                'server_timestamps': 'true',
                'doc_id': '7415498358507327',
            }
            if session:
                if cookies:
                    response = session.post(API_URL, data=data, cookies=cookies, timeout=timeout)
                else:
                    response = session.post(API_URL, data=data, timeout=timeout)
            else:
                raise ValueError("Session is None")
            
            return parse_node_reply(response.text)
        except Exception as e:
            logger.error(f"Error func get_reply_depth1_comment: {e}")
            return []
    