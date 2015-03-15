# Python bindings for edison MRAA lib
import mraa
import logging
import time
import requests
import sys
import json
import uuid

#Hydr8 Url
hurl = '192.168.7.2'


#Resistor in circuit
RESINSERIES = 560
AIO_PIN = 0
NUM_SAMPLES = 100

#no liquid
ZERO_RESISTANCE = 2000.0

#liquid at max line
CAL_RESISTANCE = 0.0

# in liquid oz
BOTTLE_VOL = 28.0

#Globals
levelSensor = mraa.Aio(AIO_PIN)

#IIOT API Stuff
#####################################
host = "dashboard.us.enableiot.com"

proxies = {
    # "https": "http://proxy.example.com:8080"
}

username = ""
password = ""
account_name = ""

#this will create a device with this id - error if it already exists
device_id = ""



verify = True # whether to verify certs

api_root = "/v1/api"
base_url = "https://{0}{1}".format(host, api_root)
device_name = "Device-{0}".format(device_id)

g_user_token = ""
g_device_token = ""

REPORT_PERIOD = 0.1

#####################################


def main():
    checkHydration()
    global g_user_token, g_device_token
    logging.basicConfig(filename='log.log', level=logging.INFO)
    logging.info('--------------------Logger Initiated--------------------')

    # Read config info from a file
    with open('config.txt','r') as configf:
        username = configf.readline().strip()
        password = configf.readline().strip()        
        account_name = configf.readline().strip()
        device_id = "57798f4b-2b1c-5cea-84f1-ac45bf6a1010"

    #Kill this on release
    logging.info("Loaded info %s,%s,%s,%s",username,password,account_name,device_id)

    g_user_token = get_token(username, password)
    logging.info("user token:%s", g_user_token)
    
    uid = get_user_id()
    logging.info("UserId: %s",format(uid))

    aid = get_account_id(uid, account_name)
    logging.info("AccountId: %s",format(aid))

    #Check response of this
    #create_device(aid, device_id, device_name)

    # refresh the activation code. It can be used any number of times
    # in the next 60 minutes to activate devices.
    ac = generate_activation_code(aid)
    logging.info("Activation code: %s",format(ac))

    # activate the device. This returns an authentication token that the device
    # can use to register time series and send observations. It will be put in
    # every header for device calls by get_device_headers(). You MUST persist
    # this is you want to send additional observations at a later time.
    g_device_token = activate(aid, device_id, ac)
    
    cid = create_component(aid, device_id, "temperature.v1.0", "water-level")

    for i in range(0,5000):
        create_observation(aid, device_id, cid)
        print i

    # while True:        
    #     print '---'
    #     averageBuf = []    
    #     for __ in range(0,NUM_SAMPLES):
    #         currentLevel = getLiquidLevel()
            
    #         while currentLevel is None:
    #             currentLevel = getLiquidLevel()        
            
    #         averageBuf.append(currentLevel)
    #     print sum(averageBuf)/NUM_SAMPLES
    #     time.sleep(0.5)


    # Buffer liquid level

    # Make Post request to intel server

# def pushtoIIOT(chunk, username, pass, devID):
#     """ Push Data chunk to intel's IOT cloud analytics"""
#     host = 'dashboard.us.enableiot.com' 

#     api_root = "/v1/api"
#     base_url = "https://{0}{1}".format(host, api_root)
#     device_name = "Device-{0}".format(device_id)

#     g_user_token = ""
#     g_device_token = ""

def checkHydration():
    """ make post request to server asking if should drink """
    #Http headers
    h = {

    }
    r = requests.post(hurl, headers=h)

    callback = True
    if callback:
        x = mraa.Gpio(13)
        x.dir(mraa.DIR_OUT)
        x.write(1)
        time.sleep(2)
        x.write(0)

def getLiquidLevel():
    """ Get's value from the sensor and does math"""    
        # Get the value from the sensor
    tempRead = levelSensor.read()

    try:
        # Conver to resistance        
        resVal = (1023.0/tempRead)-1.0
        resistance = RESINSERIES / resVal
        
        scale = (ZERO_RESISTANCE - resistance) / (ZERO_RESISTANCE - CAL_RESISTANCE)
        return BOTTLE_VOL * scale
    except:
        return None           


# Create several observations and submit them
# Create {observations_per_hour} observations per hour for {days_of_data} days
def create_observation(account_id, device_id, cid):
    url = "{0}/data/{1}".format(base_url, device_id)
    now = int(time.time()) * 1000;
    start = now - 1 * 24 * 60 * 60 * 1000
    body = {
        "on": start,
        "accountId": account_id,
        "data": []
    }
    # n observation per hour per day
    for i in range(0,10):
        
        #Get value here from sensor
        val = getLiquidLevel()

        #print "val={0}".format(val)
        o = {
            "componentId": cid,
            "on": start + i * (60 / 1) * 60 * 1000,
            "value": str(val),
            "attributes": {
                "i": i
            }
        }
        body["data"].append(o)
        time.sleep(REPORT_PERIOD)
        print 'observation made: {}'.format(val)
    data = json.dumps(body)
    #print "data={0}".format(data)
    resp = requests.post(url, data=data, headers=get_device_headers(), proxies=proxies, verify=verify)
    check(resp, 201)


## Below taken from intel docs for ease

def get_user_headers():
    headers = {
        'Authorization': 'Bearer ' + g_user_token,
        'content-type': 'application/json'
    }
    #print "Headers = " + str(headers)
    return headers


def get_device_headers():
    headers = {
        'Authorization': 'Bearer ' + g_device_token,
        'content-type': 'application/json'
    }
    #print "Headers = " + str(headers)
    return headers


def check(resp, code):
    if resp.status_code != code:
        print "Expected {0}. Got {1} {2}".format(code, resp.status_code, resp.text)
        sys.exit(1)


# Given a username and password, get the user token
def get_token(username, password):
    url = "{0}/auth/token".format(base_url)
    headers = {'content-type': 'application/json'}
    payload = {"username": username, "password": password}
    data = json.dumps(payload)
    resp = requests.post(url, data=data, headers=headers, proxies=proxies, verify=verify)
    check(resp, 200)
    js = resp.json()
    token = js['token']
    return token


# given a user token, get the user_id
def get_user_id():
    url = "{0}/auth/tokenInfo".format(base_url)
    resp = requests.get(url, headers=get_user_headers(), proxies=proxies, verify=verify)
    check(resp, 200)
    js = resp.json()
    #print js
    user_id = js["payload"]["sub"]
    return user_id


# given a user_id, get the account_id of the associated account with account_name
# if there are multiple accounts with the same name, return one of them
def get_account_id(user_id, account_name):
    url = "{0}/users/{1}".format(base_url, user_id)
    resp = requests.get(url, headers=get_user_headers(), proxies=proxies, verify=verify)
    check(resp, 200)
    js = resp.json()
    if 'accounts' in js:
        accounts = js["accounts"]
        for k, v in accounts.iteritems():
            if 'name' in v and v["name"] == account_name:
                return k
    print "Account name {0} not found.".format(account_name)
    print "Available accounts are: {0}".format([v["name"] for k, v in accounts.iteritems()])
    return None


# create a device
def create_device(account, device_id, device_name):
    url = "{0}/accounts/{1}/devices".format(base_url, account)
    device = {
        "deviceId": str(device_id),
        "gatewayId": str(device_id),
        "name": device_name,
        "tags": ["US", "California", "San Francisco"],
        # if the device will be static, use this
        # to remember where you put it
        #"loc": [37.783944, -122.401289, 17],
        "attributes": {
            "vendor": "intel",
            "platform": "x86",
            "os": "linux"
        }
    }
    data = json.dumps(device)
    resp = requests.post(url, data=data, headers=get_user_headers(), proxies=proxies, verify=verify)
    check(resp, 201)
    return resp


# Generate an activation code and return it
# This activation code will be good for 60 minutes
def generate_activation_code(account_id):
    url = "{0}/accounts/{1}/activationcode/refresh".format(base_url, account_id)
    resp = requests.put(url, headers=get_user_headers(), proxies=proxies, verify=verify)
    check(resp, 200)
    js = resp.json()
    activation_code = js["activationCode"]
    return activation_code


# Activate a device using a valid activation code
def activate(account_id, device_id, activation_code):
    url = "{0}/accounts/{1}/devices/{2}/activation".format(base_url, account_id, device_id)
    activation = {
        "activationCode": activation_code
    }
    data = json.dumps(activation)
    resp = requests.put(url, data=data, headers=get_user_headers(), proxies=proxies, verify=verify)
    check(resp, 200)
    js = resp.json()
    if "deviceToken" in js:
        token = js["deviceToken"]
        return token
    else:
        print js
        sys.exit(1)


# Given an account_id and device_id, and a component type name and name - create a component and return the cid
def create_component(account_id, device_id, component_type_name, name):
    url = "{0}/accounts/{1}/devices/{2}/components".format(base_url, account_id, device_id)
    component = {
        "type": component_type_name,
        "name": name,
        "cid": str(uuid.uuid4())
    }
    data = json.dumps(component)
    resp = requests.post(url, data=data, headers=get_device_headers(), proxies=proxies, verify=verify)
    check(resp, 201)
    js = resp.json()
    return js["cid"]




#get_observations
def get_observations(account_id, device_id, component_id):
    url = "{0}/accounts/{1}/data/search".format(base_url, account_id)
    search = {
        "from": 0,
        "targetFilter": {
            "deviceList": [device_id]
        },
        "metrics": [
            {
                "id": component_id
            }
        ]
        # This will include lat, lon and alt keys
        #,"queryMeasureLocation": True
    }
    data = json.dumps(search)
    resp = requests.post(url, data=data, headers=get_user_headers(), proxies=proxies, verify=verify)
    check(resp, 200)
    js = resp.json()
    return js


# print all of the device names and observation counts, sorted by device name
def print_observation_counts(js):  # js is result of /accounts/{account}/data/search
    if 'series' in js:
        series = js["series"]
        series = sorted(series, key=lambda v: v["deviceName"])
        for v in series:
            print "Device: {0} Count: {1}".format(v["deviceName"], len(v["points"]))


if __name__ == "__main__":
    main()