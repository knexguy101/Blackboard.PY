import requests
import pickle
import urllib
from lxml import html
import cookiejar
import bs4
import json
import time

class DuoHelper:
    def __init__(self, loginUrl, sig, host, session):
        self.loginUrl = loginUrl
        self.sig = sig
        self.host = host
        self.s = session
        self.duoHeaders = {
            "Connection": "keep-alive",
            "Accept": "text/plain, */*; q=0.01",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        }
        
    def duoLogin(self):
        formData = self.getCookieForm()
        status, sid = self.getCookie(formData)
        if(status == "logged_in"):
            return sid
        else:
            formData = self.getCookieForm()
            status, sid = self.getCookie(formData)
            txid = self.call(sid)
            resultURL = self.getStatus(sid, txid)
            cookie, parent = self.getAuthCookie(sid, resultURL)
            return cookie, parent
    
    def getCookieForm(self):
        r = self.s.get("https://%s/frame/web/v1/auth?tx=%s&parent=%s" % (self.host, self.sig.split(':')[0], self.loginUrl), headers={
            "Connection": "keep-alive",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "nested-navigate",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": self.loginUrl
        })
        
        form_list = {}
        soup = bs4.BeautifulSoup(r.content, "lxml")
        scripts = soup.find_all('input')
        for script in scripts:
            form_list[script["name"]] = script["value"]
        return form_list
        
    def getCookie(self, formData):
        
        sigFix = formData[list(formData.keys())[0]]
        loginUrlFix = formData[list(formData.keys())[1]]
        
        self.duoHeaders["Referer"]: "https://%s/frame/web/v1/auth?tx=%s&parent=%s" % (self.host, sigFix, loginUrlFix)
        self.duoHeaders["Origin"]: self.host
        
        formData["java_version"] = ""
        formData["flash_version"] = ""
        formData["screen_resolution_width"] = 1920
        formData["screen_resolution_height"] = 1080
        formData["color_depth"] = 24
        formData["is_cef_browser"] = "false"
        formData["is_ipad_os"] = "false"
        
        print(formData)
        
        r = self.s.post("https://%s/frame/web/v1/auth?tx=%s&parent=%s" % (self.host, sigFix, loginUrlFix),headers={
            "Connection": "keep-alive",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "nested-navigate",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://%s/frame/web/v1/auth?tx=%s&parent=%s" % (self.host, sigFix, loginUrlFix),
            "Origin": self.host,
            "Content-Type": "application/x-www-form-urlencoded",
            "Upgrade-Insecure-Requests": "1"
        }, data = formData)
        
        soup = bs4.BeautifulSoup(r.content, "lxml")
        print(r.content)
        try:
            return "new_login", soup.find("input", {"name": "sid"})["value"]
        except:
            return "logged_in", soup.find("input", {"name": "js_cookie"})["value"]
        
    def call(self, sid):
        data = {
            "sid": sid,
            "device": "phone1",
            "factor": "Phone Call",
            "out_of_date": "",
            "days_out_of_date": "",
            "days_to_block": "None"
        }

        r = self.s.post("https://%s/frame/prompt" % (self.host), headers=self.duoHeaders, data=data)
        print(r.content)
        r = r.json()
        return r["response"]["txid"]
    
    def getStatus(self, sid, txid):
        while(True):
            data = {
                "sid": sid,
                "txid": txid
            }

            r = self.s.post("https://%s/frame/status" % (self.host), headers=self.duoHeaders, data=data)
            print(r.content)
            r = r.json()

            try:
                if(r["response"]["status_code"] == "answered"):
                    print("------------\n- Press %s on your phone -\n--------------" % (r["response"]["msg_info"].get("key")))
                    time.sleep(1)
                elif(r["response"]["result"] == "SUCCESS"):
                    break
                elif(r["response"]["result"] == "ERROR"):
                    break
                else:
                    time.sleep(1)
            except Exception as e:
                time.sleep(1)
        
        return r["response"]["result_url"]
    
    def getAuthCookie(self, sid, resultUrl):
        
        self.duoHeaders["Referer"] = "https://%s/frame/prompt?sid=%s" % (
            self.host,
            sid
        )
        
        data = {
            "sid": sid
        }
        
        r = self.s.post("https://" + self.host + resultUrl, headers=self.duoHeaders, data=data)
        r = r.json()
        with open('temp.txt', 'w') as f:
            json.dump(requests.utils.dict_from_cookiejar(self.s.cookies), f)
        return r["response"]["cookie"], r["response"]["parent"]