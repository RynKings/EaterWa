import requests
import json
import os
import shutil
import re
import urllib
import traceback

from collections import namedtuple

def loggedIn(func):
    def checkLogin(*args, **kwargs):
        if args[0].isLogin:
            return func(*args, **kwargs)
        else:
            print('You want to call the function, you must login to Whatsapp')
    return checkLogin

# class Json2Object:

class Json2Object(object):
    def __init__(self, d):
        if type(d) is str:
            d = json.loads(d)

        self.from_dict(d)

    def from_dict(self, d):
        self.__dict__ = {}
        for key, value in d.items():
            if type(value) is dict:
                value = Json2Object(value)
            self.__dict__[key] = value

    def to_dict(self):
        d = {}
        for key, value in self.__dict__.items():
            if type(value) is Json2Object:
                value = value.to_dict()
            d[key] = value
        return d

    def __repr__(self):
        return json.dumps(self.to_dict(), indent=4, sort_keys=True)

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

class EaterWa(object):

    isLogin = False

    def __init__(self, json_auth):

        self.host = 'https://wa.boteater.us/api'
        self._session = requests.session()

        if isinstance(json_auth, dict):
            self.headers = json_auth
        else:
            raise Exception('Invalid Authentication !!!')

    def login(self):
        getCl = self.getClient()
        if getCl.status == 406:
            raise Exception('Invalid Headers !!!')
        qr = self.getQr()
        try:
            print('Scan this QR : ', qr.result['qr-callback'])
        except:
            print('Trying to login...')

        try:
            callback = self.j2o(self.getContent(qr.result.callback))
        except Exception as e:
            print(traceback.format_exc())
            raise Exception('Check your connection on your android or run again this program')

        if callback.result == 'LoggedIn':
            self.isLogin = True
            profile = self.getMe()
            res = 'Login success !!!'
            res += '\nName : {} '.format(profile.pushname)
            res += '\nWId : {}'.format(profile.me)
            res += '\nBattery : {}'.format(profile.battery)
            res += '\n========================'
            res += '\nPhone Name : {}'.format(profile.phone.device_manufacturer)
            res += '\nPhone model : {}'.format(profile.phone.device_model)
            res += '\nPhone OS Version : {}'.format(profile.phone.os_version)
            res += '\nWhatsapp Version : {}'.format(profile.phone.wa_version)
            print(res)
            return True
        else:
            self.isLogin = False
            print(callback.result)
            return False

    def j2o(self, text):
        try:
            _dict = text.text
            return Json2Object(_dict)
        except Exception as e:
            raise Exception("Error : {}\n\nResponse : {}".format(str(e), text.text))

    def urlEncode(self, url, path, params=[]):
        return url + path + '?' + urllib.parse.urlencode(params)

    def getContent(self, url, headers=None):
        if headers is None:
            headers = self.headers
        return self._session.get(url, headers=headers, stream=True)

    def postContent(self, url, data=None, files=None, headers=None):
        if headers is None:
            headers = self.headers
        return self._session.post(url, headers=headers, data=data, files=files)

    def downloadFileWithURL(self, url, filename):
        files = open(filename, 'wb')
        resp  = requests.get(url, stream=True)
        resp.raw.decode_content = True
        shutil.copyfileobj(resp.raw, files)
        return filename

    def getClient(self):
        url = self.host + '/client'
        a = self.getContent(url)
        return self.j2o(a)

    def getQr(self):
        url = self.host + '/login'
        a = self.getContent(url)
        return self.j2o(a)

    @loggedIn
    def getMe(self):
        url = self.host + '/getMe'
        a = self.getContent(url)
        return self.j2o(a)

    @loggedIn
    def getUnread(self, me=True, notif=True):
        data = {
            'include_me': me,
            'include_notifications': notif
        }
        req = self.postContent(self.host + '/unread', data=data)
        return self.j2o(req)

    @loggedIn
    def getContact(self, userid):
        url = self.host + '/getContact'
        data = {
            'userid': userid
        }
        req = self.postContent(url, data=data)
        return self.j2o(req)

    @loggedIn
    def getContacts(self):
        url = self.host + '/getContacts'
        a = self.getContent(url)
        return self.j2o(a)

    @loggedIn
    def getMyContacts(self):
        url = self.host + '/getMyContacts'
        a = self.getContent(url)
        return self.j2o(a)

    @loggedIn
    def getWaVersion(self):
        url = self.host + '/getWaVersion'
        a = self.getContent(url)
        return self.j2o(a)

    @loggedIn
    def getGroupLink(self, to):
        url = self.host + '/getGroupLink'
        data = {
            'chat_id': to
        }
        a = self.postContent(url, data=data)
        return self.j2o(a)

    @loggedIn
    def revokeGroupLink(self, to):
        url = self.host + '/revokeGroupLink'
        data = {
            'chat_id': to
        }
        a = self.postContent(url, data=data)
        return self.j2o(a)

    @loggedIn
    def simulateTyping(self, to, on):
        url = self.host + '/simulateTyping'
        data = {
            'chat_id': to,
            'on': on
        }
        a = self.postContent(url, data=data)
        return self.j2o(a)

    @loggedIn
    def sendMessage(self, to, text):
        url = self.host + '/sendMessage'
        data = {
            'chat_id': to,
            'message': text
        }
        self.simulateTyping(to, True)
        req = self.postContent(url, data=data)
        self.simulateTyping(to, False)
        return self.j2o(req)

    @loggedIn
    def sendMessageV2(self, to, text, metadata={}):
        url = self.host + '/sendMessageV2'
        data = {
            'chat_id': to,
            'message': text,
            'metadata': str(metadata)
        }
        self.simulateTyping(to, True)
        req = self.postContent(url, data=data)
        self.simulateTyping(to, False)
        return self.j2o(req)

    @loggedIn
    def sendMention(self, to, text, userids=[]):
        url = self.host + '/sendMention'
        data = {
            'chat_id': to,
            'message': text,
            'user_ids': userids
        }
        self.simulateTyping(to, True)
        req = self.postContent(url, data=data)
        self.simulateTyping(to, False)
        return self.j2o(req)

    @loggedIn
    def sendMedia(self, to, path, caption='', metadata={}, mentionedJidList=[]):
        url = self.host + '/sendMedia'

        msgMetaData = {}
        if metadata:
            msgMetaData.update(metadata)
        if mentionedJidList:
            msgMetaData.update({'mentionedJidList': mentionedJidList})
        data = {
            'chat_id': to,
            'caption': caption,
            'metadata': str(metadata)
        }
        files ={'files': open(path,'rb')}
        req = self.postContent(url, data=data, files=files)
        return self.j2o(req)

    @loggedIn
    def sendContact(self, to, user_id):
        url = self.host + '/sendContact'
        data = {
            'chat_id': to,
            'user_id': user_id
        }
        req = self.postContent(url, data=data)
        return self.j2o(req)

    @loggedIn
    def sendVcard(self, to, displayName, vcard):
        url = self.host + '/sendVCard'
        data = {
            'chat_id': to,
            'displayName': displayName,
            'vcard': vcard
        }
        req = self.postContent(url, data=data)
        return self.j2o(req)

    @loggedIn
    def sendMediaWithURL(self, to, url, filename, caption='', metadata={}):
        path = self.downloadFileWithURL(url, filename)
        r = self.sendMedia(to, path, caption, metadata)
        os.remove(path)
        return r

    @loggedIn
    def sendSeen(self, to):
        url = self.host + '/sendSeen'
        data = {
            'chat_id': to
        }
        req = self.postContent(url, data=data)
        return self.j2o(req)

    @loggedIn
    def sendReply(self, message_id, text):
        url = self.host + '/sendReply'
        data = {
            'message_id': message_id,
            'message': text
        }
        req = self.postContent(url, data=data)
        return self.j2o(req)

    @loggedIn
    def getBatteryLevel(self):
        url = self.host + '/getBatteryLevel'
        req = self.getContent(url)
        return self.j2o(req)

    @loggedIn
    def getGroupParticipantsIds(self, to):
        url = self.host + '/getGroupParticipantsIds'
        data = {
            'group_id': to
        }
        req = self.postContent(url, data=data)
        return self.j2o(req)

    @loggedIn
    def revoke(self):
        url = self.host + '/revoke'
        req = self.getContent(url, params=self.headers)
        return self.j2o(req)

    @loggedIn
    def mentionAll(self, message):
        to = message['chatId']
        myId = self.getMe().me
        if message['chat']['isGroup']:
            result = '╭───「 Mention Members 」\n'
            no = 0
            members = self.getGroupParticipantsIds(message['chatId']).result
            if myId in members:
                members.remove(myId)
            for member in members:
                no += 1
                result += '│ %i. @%s\n' % (no, member.replace('@c.us',''))
            result += '╰───「 Hello World 」\n'
            self.sendMention(to, result, members)
        else:
            self.sendMessage(to, 'Group only!')
