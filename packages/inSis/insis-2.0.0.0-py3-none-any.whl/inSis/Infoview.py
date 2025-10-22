import requests
import hashlib
import base64
import json
import datetime

def CheckServer(dmname):
    print("Checking the Server Connection..")
    try:
        reqUrl=dmname+"/inSis/api/InfoviewApp/CheckServer"
        webresponse = requests.get(reqUrl)
        webRequestContent = webresponse.json()
        sts = webRequestContent['Status']
        if(sts):
            return True
        else:
            return False
    except requests.exceptions.ConnectionError:
        print("Connection Error")
        return False
    except requests.exceptions.HTTPError:
        print("HTTP Error..")
        return False
    except BaseException as ex:
        print(ex)
        return False

def CheckUserCredentials(server,uname,pdname):
    print("Checking Credentials...")
    try:
        if(uname!="" and pdname!=""):
            usr_encode = base64.b64encode(uname.encode()).decode()
            password_bytes = pdname.encode('utf-8')
            sha512_hash = hashlib.sha512(password_bytes).digest()
            base64_hash = base64.b64encode(sha512_hash).decode('utf-8')
            pd_encode=base64.b64encode(base64_hash.encode()).decode()
            usrdetails = usr_encode+","+ pd_encode
            reqUrl = server+"/inSis/api/InfoviewApp/CheckUserCredentials?Userdetails="+usrdetails+"&uname="+uname+"&AppMode=Python Package"
            webresponse = requests.get(reqUrl)
            webRequestContent = webresponse.json()
            sts = webRequestContent['Status']
            if(sts):
                return True
            else:
                print("Credentials Invalid..")
                return False
        else:
            print("Username and PassWord should not be Empty.Please check..")
    except requests.exceptions.ConnectionError:
        print("Connection Error")
        return False
    except requests.HTTPError:
        print("HTTP Error")
        return False
    except BaseException as ex:
        print(ex)
        return False

class Infoview():
    def __init__(self):
        self.Servername=None
        self.username=None
        self.pdname=None
        self.apikey=None
        self.clientId=None
    def __init__(self,Servername,username,pdname,apikey,clientId):
        try:
            self.Servername=Servername
            self.username=username
            self.pdname=pdname
            self.apikey=apikey
            self.clientId=clientId
            ServerResult=CheckServer(Servername)
            if(ServerResult):
                print("Server Connected Successfully..")
                CredentialsResult=CheckUserCredentials(Servername,username,pdname)
                if(CredentialsResult):
                    print("Credentials Valid..")
                else:
                    print("Credentials Invalid..")
            else:
                print("Server Connection is Failed..")
        except requests.exceptions.ConnectionError:
            print("Connection Error..")
        except requests.HTTPError:
            print("HTTP Error..")
        except BaseException as ex:
            print(ex)         

    def GetCurrentData(self,tagnames):
        print("Getting the Current Data information...")
        resArr=[]
        try:
            if(tagnames!=""):
                server=self.Servername
                usr=self.username
                pwd=self.pdname
                apikey=self.apikey
                clientId=self.clientId
                requrl=server+"/insis/api/data/getcurrent?clientId="+clientId+"&tagnames="+tagnames                
                headers = {"insis_api_key":apikey,"insis_api_user":usr,"insis_api_pwd":pwd}
                response = requests.post(requrl,headers=headers)                
                responseResult = response.content.decode('utf-8')
                resArr = json.loads(responseResult)                
                return resArr
            else:
                print("TagNames sholud not be the empty..")
                return resArr
        except requests.exceptions.ConnectionError:
            print("Connection Error..")
            return resArr
        except requests.HTTPError:
            print("HTTP Error")
            return resArr
        except BaseException as ex:
            print(ex)
            return resArr
    def GetHistoryData(self,tagnames,interval,aggregate,st,et):
        print("Getting the History Data..")
        reshis=[]
        try:
            server=self.Servername
            usr=self.username
            pwd=self.pdname
            apikey=self.apikey
            clientId=self.clientId
            requrl=server+"/insis/api/data/GetHistory?clientId="+clientId+"&tagnames="+tagnames+"&Interval="+interval+"&Aggregate="+aggregate+"&ST="+st+"&ET="+et
            headers={"insis_api_key":apikey,"insis_api_user":usr,"insis_api_pwd":pwd}
            response = requests.post(requrl,headers=headers)
            responseResult = response.content.decode('utf-8')
            reshis = json.loads(responseResult)  
         
            return reshis
        except requests.exceptions.ConnectionError:
            print("Connection Error..")
            return reshis
        except requests.HTTPError:
            print("HTTP Error")
            return reshis
        except BaseException as ex:
            print(ex)
            return reshis
    def SetManualData(self,publishdata):
        print("Publishing the Manual Data..")
        resSetData=[]
        try:
            server=self.Servername
            usr=self.username
            pwd=self.pdname
            apikey=self.apikey
            clientId=self.clientId
            my_PubData = str(publishdata)
            requrl=server+"/insis/api/data/PublishData?clientId="+clientId+"&Data="+my_PubData
            headers={"insis_api_key":apikey,"insis_api_user":usr,"insis_api_pwd":pwd}
            response = requests.post(requrl,headers=headers)
            responseResult = response.content.decode('utf-8')
            resSetData = json.loads(responseResult)           
            return resSetData
        except requests.exceptions.ConnectionError:
            print("Connection Error...")
            return resSetData
        except requests.HTTPError:
            print("HTTP Error..")
            return resSetData
        except BaseException as ex:
            print(ex)
            return resSetData

    def GetRawData(self,tagnames,st,et):
        print("Getting the Raw Data..")
        resrawData=[]
        try:
            server=self.Servername
            usr=self.username
            pwd=self.pdname
            apikey=self.apikey
            clientId=self.clientId
            requrl=server+"/insis/api/data/GetRaw?clientId="+clientId+"&tagnames="+tagnames+"&ST="+st+"&ET="+et
            headers={"insis_api_key":apikey,"insis_api_user":usr,"insis_api_pwd":pwd}
            response = requests.post(requrl,headers=headers)
            responseResult = response.content.decode('utf-8')
            resrawData = json.loads(responseResult)
            return resrawData
        except requests.exceptions.ConnectionError:
            print("Connection Error..")
            return resrawData
        except requests.HTTPError:
            print("HTTP Error")
            return resrawData
        except BaseException as ex:
            print(ex)
            return resrawData

    def GetBatchAnalysis(self,tagnames,st,et):
        print("Getting the Batch Analysis Data..")
        resbatch=[]
        try:
            server=self.Servername
            usr=self.username
            pwd=self.pdname
            apikey=self.apikey
            clientId=self.clientId
            requrl=server+"/insis/api/data/GetBatchAnalysis?clientId="+clientId+"&tagnames="+tagnames+"&ST="+st+"&ET="+et
            headers={"insis_api_key":apikey,"insis_api_user":usr,"insis_api_pwd":pwd}
            response = requests.post(requrl,headers=headers)
            responseResult = response.content.decode('utf-8')
            resbatch = json.loads(responseResult)
            return resbatch
        except requests.exceptions.ConnectionError:
            print("Connection Error..")
            return resbatch
        except requests.HTTPError:
            print("HTTP Error")
            return resbatch
        except BaseException as ex:
            print(ex)
            return resbatch
            

            

 
    
