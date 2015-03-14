# Python bindings for edison MRAA lib
#import mraa
import logging
import time
import requests
from IIOT import *

#Resistor in circuit
RESINSERIES = 560
AIO_PIN = 1
NUM_SAMPLES = 1000

#Globals
#levelSensor = mraa.Aio(AIO_PIN)

def main():
    global g_user_token, g_device_token

    logging.basicConfig(filename='log.log', level=logging.INFO)
    logging.info('--------------------Logger Initiated--------------------')

    # Read config info from a file
    with open('config.txt','r') as configf:
        username = configf.readline().strip()
        password = configf.readline().strip()        
        account_name = configf.readline().strip()
        device_id = "57798f4b-2b1c-4cea-84f1-ac45bf6a1069"

    #Kill this on release
    logging.info("Loaded info %s,%s,%s,%s",username,password,account_name,device_id)

    g_user_token = get_token(username, password)
    logging.info("user token:%s", g_user_token)
    uid = get_user_id()
    logging.info("UserId: {0}",format(uid))


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


def getLiquidLevel():
    """ Get's value from the sensor and does math"""    
    
    try:        
        rawVal = levelSensor.read()
    except:
        print ("AIO Error")
        return None

    #Prevent div-by-zero
    if rawVal == 0:
        return None

    #Math for liquid level
    try:
        # Conver to resistance
        resVal = (1023.0/rawVal) -1
        resVal = RESINSERIES / resVal

        # Do math (based on chart from adafruit eTape datasheet)
        
        #time.sleep(0.5)        
        return resVal
    except:
        return None



if __name__ == "__main__":
    main()