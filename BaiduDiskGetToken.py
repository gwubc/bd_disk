import requests
import json


# Step 1
# client_id = "xxx"
# client_secret = "xxx"
#
# url = f"http://openapi.baidu.com/oauth/2.0/authorize?response_type=code&client_id={client_id}&redirect_uri=oob&scope=basic,netdisk"
# print(url)  # Go to url, login, get code.
#
# Step 2
# code = "xxx"
#
# url = f"https://openapi.baidu.com/oauth/2.0/token?grant_type=authorization_code&code={code}&client_id={client_id}&client_secret={client_secret}&redirect_uri=oob"
# response = requests.get(url, headers={'User-Agent': 'pan.baidu.com'})
# response = json.loads(response.text.encode('utf8'))
