import requests
import urllib
from lxml import html
import cookiejar
import bs4
import json
from helpers.duoHelper import DuoHelper

class BlackboardClient:
    def __init__(self, loginUrl, username, password):
        self.s = requests.Session()
        self.loginUrl = loginUrl
        self.username = username
        self.password = password
        self.blackboardHeaders = {
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36",
            "Sec-Fetch-User": "?1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Referer": self.loginUrl,
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9"
        }
        self.duoHeaders = {
            "Connection": "keep-alive",
            "Accept": "text/plain, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
    def getFormToken(self):
        r = self.s.get(self.loginUrl)
        soup = bs4.BeautifulSoup(r.content, "lxml")
        formKey = soup.find("input", {"name": "csrfmiddlewaretoken"})["value"]
        return formKey
    
    def postUsername(self):
        token = self.getFormToken()
        data = {
            "csrfmiddlewaretoken": token,
            "username": self.username
        }
        r = self.s.post(self.loginUrl, headers=self.blackboardHeaders, data=data)
        soup = bs4.BeautifulSoup(r.content, "lxml")
        try:
            password = soup.find('input', {"id": "password"})
            if(password["name"] != "password"):
                return False
            else:
                return True
        except:
            return False
        
    def postPassword(self):
        token = self.getFormToken()
        data = {
            "csrfmiddlewaretoken": token,
            "username": self.username,
            "password": self.password
        }
        r = self.s.post(self.loginUrl, headers=self.blackboardHeaders, data=data)
        soup = bs4.BeautifulSoup(r.content, "lxml")
        try:
            scripts = soup.find_all('script')
            for script in scripts: 
                if "Duo.init" in script.text:
                    raw = script.text.split('(')[1].split(')')[0].replace("'", '"')
                    raw = raw.split(',')[0:2]
                    raw = ",".join(raw) + "}"
                    return raw
            return "Error"
        except Exception as e:
            return "Error %s" % (e)
        
    def formatPasswordResponse(self, passwordRaw):
        j = json.loads(passwordRaw)
        return j["host"], j["sig_request"]
    
    def loadSampleCookies(self):
        with open('temp.txt', 'r') as f:
            try:                
                cookies = requests.utils.cookiejar_from_dict(json.load(f))
                self.s.cookies.update(cookies)
            except Exception as e:
                print(e)
            
    
    def doDuoSecurity(self, host, sig_request):
        duoMobile = DuoHelper(self.loginUrl, sig_request, host, self.s)
        self.loadSampleCookies()
        authToken = duoMobile.duoLogin()
        r = self.s.get("https://tamu.blackboard.com/webapps/portal/execute/tabs/tabAction")
        print(r.content)