
import json
from .log_ import logger
def parse_end_cursor(json_data):
    try:
        cursor = json_data['data']['page_info']['end_cursor']
        return cursor
    except Exception as e:
        logger.error(f">> Error func parse_end_cursor: {e}")
        return None
def paser_node_posts_group(data):
    cursor = None
    nodes = []
    res = {}
    matches = data.split("\n")
    for i, match in enumerate(matches):
        try:
            json_match = json.loads(match)
            if i == 0:
                list_node_post = json_match['data']['node']['group_feed']['edges']   #parse("$.data.node.group_feed.edges")
                for node_post in list_node_post:
                    nodes.append(node_post['node'])
            else:
                if json_match.get("label", "") == 'GroupsCometFeedRegularStories_paginationGroup$stream$GroupsCometFeedRegularStories_group_group_feed': # in match:
                    nodes.append(json_match['data']['node'])

                elif json_match.get("label", "") == 'GroupsCometFeedRegularStories_paginationGroup$defer$GroupsCometFeedRegularStories_group_group_feed$page_info': #in match:
                    cursor = parse_end_cursor(json_match)
                else:
                    #print(f"----------")
                    pass
        except Exception as ex:
            #logger.error(f">> Error func paser_node_post_group: {ex}")
            if "rate limit" in json.dumps(data).lower():
                logger.error(">> Rate limit reached, stopping parsing.")
                break
            else:
                logger.error(f">> Error func paser_node_posts_group: {ex}")
    res['node_posts'] = nodes
    res['cursor'] = cursor
    return res
def paser_node_posts_page(data):
    cursor = None
    nodes = []
    res = {}
    matches = data.split("\n")
    #print(f">> số json trả về là {len(matches)}")
    for i, match in enumerate(matches):
        try:
            json_match = json.loads(match)
            if i == 0:
                list_node_post = json_match['data']['node']['timeline_list_feed_units']['edges']
                for node_post in list_node_post:
                    nodes.append(node_post['node'])
            else:
                if json_match.get("label", "") == 'ProfileCometTimelineFeed_user$stream$ProfileCometTimelineFeed_user_timeline_list_feed_units':
                    nodes.append(json_match['data']['node'])

                elif json_match.get("label", "") == 'ProfileCometTimelineFeed_user$defer$ProfileCometTimelineFeed_user_timeline_list_feed_units$page_info':
                    cursor = parse_end_cursor(json_match)
                else:
                    #print(f"----------")
                    pass
        except Exception as ex:
            logger.error(f">> Error func paser_node_posts_page: {ex}")
    res['node_posts'] = nodes
    res['cursor'] = cursor
    return res
def paser_node_post(data):
    res = {}
    matches = data.split("\n")
    for i, match in enumerate(matches):
        try:
            json_match = json.loads(match)
            try:
                node_post = json_match['data']['node']
            except:
                node_post = None
            if node_post: 
                if node_post['__typename'] == "Story":
                    res = node_post
                    break
        except Exception as ex:
            logger.error(f" >> Error message: {ex}")
    return res
def parse_node_comments(data):
    node_comments = []
    matches = data.split("\n")
    for i, match in enumerate(matches):
        try:
            json_match = json.loads(match)
            node_comments = json_match['data']['node']['comment_rendering_instance_for_feed_location']['comments']['edges']
        except Exception as ex:
            logger.error(f"Process  >> Error func parse_node_comments: {ex}")
    return node_comments

def parse_node_reply(data):
    node_comments = []
    matches = data.split("\n")
    for i, match in enumerate(matches):
        try:
            json_match = json.loads(match)
            node_comments = json_match['data']['node']['replies_connection']['edges']
        except Exception as ex:
            logger.error(f"Process  >> Error func parse_node_comments: {ex}")
    return node_comments