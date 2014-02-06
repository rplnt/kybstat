from sqlalchemy.orm import sessionmaker
from bs4 import BeautifulSoup as bs
from sqlalchemy import func
import HTMLParser
import datetime
import requests
import logging
import json
import time
import bs4
import re

from common.db import *
from common.config import *

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

content_tpl = {
    "id": None,
    "name": None,
    "parent": None,
    "owner": {
        "id": None,
        "name": None
    },
    "created": None,
    "views": None,
    "children": None,
    "descendants": None,
    "k": None,
    "bookmarked": None,
    "content": None
}

html_parser = HTMLParser.HTMLParser()
time_delta = datetime.timedelta(0, add_time)


class NotLoggedInException(Exception):
    pass


class WeirdResultException(Exception):
    pass

class SomethingXmlException(Exception):
    pass


def log_error(session, node, error, data=''):
    log = Log(node_id=node,
              timestamp=datetime.datetime.now(),
              error=error,
              data=data)
    session.add(log)


def login():
    params = {'login': username, 'password': password, 'login_type': 'name', 'event': 'login'}
    r = requests.post(base_url, data=params, allow_redirects=False)

    if r.status_code != 302:
        logging.error('Could not log in.')
        raise NotLoggedInException  # no one can hear you scream

    logging.info('Succesfully logged in.')

    return r.cookies


def parse_response(response):
    soup = bs(response.text)

    if soup.find('input', attrs={'value': 'login'}):
        logging.error('Not logged in!')
        raise NotLoggedInException

    if soup.find(dumpnode):
        # xml
        dump = soup.find(dumpnode)
        content = content_tpl.copy()

        # lots of exceptions, just write it out
        content['id'] = dump.id.text
        content['name'] = dump.title.text
        content['created'] = dump.created.text
        content['views'] = dump.views.text
        content['children'] = dump.childs.text
        content['descendants'] = dump.desc.text
        content['k'] = dump.k.text
        content['bookmarked'] = dump.bookmarked.text
        content['parent'] = dump.parent_id.text
        content['content'] = html_parser.unescape(dump.content.text)
        content['owner']['id'] = dump.owner.id.text
        content['owner']['name'] = dump.owner.username.text

    elif soup.find('body'):
        # most likely a private node
        
        content = content_tpl.copy()

        if not soup.text.find("you don't have permissions for viewing this data node"):
            raise WeirdResultException

        content['id'] = soup.form['action'].split('/')[-2]
        if not re.match('^\d{7}$', content['id']):
            logging.error('id %s does not look like id' % content['id'])
            raise WeirdResultException

        try:
            coords = soup.find('table', id='node_coord')
            a = coords.find('a', href='/id/%s' % content['id'])
            content['name'] = a['title']
            for tag in coords.find('a', href='/id/%s' % content['id']).previous_siblings:
                if isinstance(tag, bs4.element.Tag) and tag.name == 'a':
                    content['parent'] = tag.text
                    break
            else:
                content['parent'] = 0
                
        except IndexError:
            logging.error('No/empty title?')
            content['name'] = u''

        content['owner']['id'] = soup.find_all('center')[1].a['href'].split('/')[-1]

        try:
            content['owner']['name'] = soup.find_all('center')[1].a.text
        except (IndexError, AttributeError) as e:
            logging.error('No/empty owner name? ' + e.message)
            content['owner']['name'] = u''

    else:
        # wat
        return None

    return content


def scraper(session, start, end=final_id, delay=waittime):
    error_counter = 0
    cookie = login()

    for node_id in xrange(int(start), int(end) + 1):
        if session.query(Node).filter(Node.id == node_id).first():
            logging.info("Node %d already in the db" % node_id)
            continue
        logging.info('Processing node %d' % node_id)

        # DA GET
        url = base_url + str(node_id) + template
        response = requests.get(url, cookies=cookie)

        if response.status_code != 200:
            error_counter += 1
            logging.warning('Could not retrieve %s' % url)
            log_error(session, node_id, "Not OK", 'status: %d' % response.status_code)
            time.sleep(waittime)
            continue

        try:
            data = parse_response(response)
        # skip bad nodes
        except SomethingXmlException:
            log_error(session, node_id, 'XML Failed')
            continue
        except NotLoggedInException:
            log_error(session, node_id, 'Not logged in')
            cookie = login()
            continue
        except WeirdResultException:
            log_error(session, node_id, 'Weird node')
            continue
        except (IndexError, AttributeError) as e:
            logging.error(e.message)
            log_error(session, node_id, 'No owner id?')
            continue

        if data is None:
            logging.error('wat')
            log_error(session, node_id, 'fuckedup node')
            continue

        if data['created'] is None:
            last, = session.query(Node.created).order_by(Node.id.desc()).first()
            data['created'] = last + time_delta
            logging.warning('Private node, using old timestamp %s' % last)

        if session.query(User).filter(User.id == data['owner']['id']).first():
            pass
        else:
            logging.info("New user: %s [%s]" % (data['owner']['name'], data['owner']['id']))
            owner = User(id=data['owner']['id'], name=data['owner']['name'])
            session.add(owner)
            session.commit()

        if data['owner']['id'] == 332:
            log_error(session, node_id, 'bot', data['content'])
            continue

        node = Node(data)
        session.add(node)
        session.commit()

        logging.info('Inserted node %d by owner %s [%s] into db' %
                     (node_id, data['owner']['name'], data['owner']['id']))

        if error_counter > 8:
            logging.error('err cunt')
            log_error('Error counter', node_id)
            break

        time.sleep(waittime)


def setup():
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == '__main__':
    session = setup()

    # continue where we left
    start, = session.query(func.max(Node.id)).first()
    start = first_id if start is None else start

    scraper(session, start)
