import requests
import json
import sys, os
from airtable import AirtableClientFactory, AirtableSorter, SortDirection
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    ## slackid 列がブランクになっているairtableのデータを取得
    airtabledata = []
    airtabledata = getAirTable()

    ## データがなければ終了
    if not airtabledata:
        return 
    
    ## 書き込むデータを作成する
    write_airtable_all_data = []
    write_airtable_all_data = createWriteData(airtabledata)
    
    logger.info(write_airtable_all_data)
    ## airtableにデータを書き込み
    for writedata in write_airtable_all_data:
    	recordid = writedata[0]
    	slackid = writedata[1]
    	kotid = writedata[2]
    	
    	updateAirTable(recordid, slackid, kotid)
    
    response = {
      "text": "終了しました",
    }

    return response

## 関数
## airtableのデータを読み出す
def getAirTable():
    airtableBaseKey = os.environ['AIRTABLE_BASE_KEY']
    airtableApiKey = os.environ['AIRTABLE_API_KEY']

    atf = AirtableClientFactory(base_id=airtableBaseKey, api_key=airtableApiKey)
    at = atf.create('EmployeeDirectory')

    # slackid列がブランクのデータを取得
    atRecord = at.get_all_by('slack_id', '', view='All_employees').get()

    # recordid, email, 従業員番号を1つのデータとしてブランクになっている人数分取得する
    addAllList = []
    
    if not atRecord:
        logger.info("ブランクはありません")
        return 
    
    elif type(atRecord) is dict:
        logger.info("dict型で1データのみです")
        add1List = []
        rec = atRecord
        recordid = rec.get('id')
        email = rec.get('fields').get('Email address')
        id = rec.get('fields').get('Employee_id')
        add1List.append(recordid)
        add1List.append(id)
        add1List.append(email)
        # 1人分のデータをまとめて入れる
        addAllList.append(add1List)
        
        return addAllList
    
    elif type(atRecord) is list:
        logger.info("list型で複数データのみです")
        
        for rec in atRecord:
            add1List = []
            recordid = rec.get('id')
            email = rec.get('fields').get('Email address')
            id = rec.get('fields').get('Employee_id')
            add1List.append(recordid)
            add1List.append(id)
            add1List.append(email)
            # 1人分のデータをまとめて入れる
            addAllList.append(add1List)
        return addAllList
    
    else:
        logger.info("atRecordにdict, list型以外のデータが使われています")
        return

## 書き込むデータを作成する
def createWriteData(airtabledata):
    _write_airtable_all_data = []
    
    # recordid, slackid, employeeidを１つのデータとして書き込む人数分データを作成する
    for data in airtabledata:
        write_airtable_1_data = []

        employeenumber = data[1]
        email = data[2]
        recordid = data[0]
        slackid = getSlackId(email)
        
        ## slackidが取れなければ終了
        if slackid == '':
            logger.info("SlackIDが取得できませんでした")
            return
        
        employeeid = getKotEmployKey(employeenumber)

        write_airtable_1_data.append(recordid)
        write_airtable_1_data.append(slackid)
        write_airtable_1_data.append(employeeid)

        _write_airtable_all_data.append(write_airtable_1_data)

    return _write_airtable_all_data

## slackidを取得する
def getSlackId(email):
    url = "https://slack.com/api/users.lookupByEmail"
    slackBotToken = os.environ['SLACK_BOT_TOKEN']

    payload = {
        'content-type': "application/json",
        'token': slackBotToken,
        'email': email
        }

    response = requests.request("GET", url, params=payload)
    userinfo = json.loads(response.text)
  
    if userinfo['ok'] != 'False':
    	slackid = userinfo.get('user').get('id')
    	return slackid
    else:
        logger.info("slackユーザがありませんでした")
        return

## employeekey を取得する
def getKotEmployKey(code):
    url = "https://api.kingtime.jp/v1.0/employees"
    kotToken = os.environ['KOT_TOKEN']
    
    headers = {
        'Authorization': "Bearer " + kotToken,
        'content-type': "application/json",
        }

    userData = {
        "additionalFields": 'currentDateEmployee',
    }

    response = requests.request("GET", url, headers=headers)
    a = json.loads(response.text)

    for item in a:
        if(item["code"] == code):
            return item["key"]

# airtableに書き込む
def updateAirTable(recordid, slackid, kotid):
    airtableBaseKey = os.environ['AIRTABLE_BASE_KEY']
    airtableApiKey = os.environ['AIRTABLE_API_KEY']

    atf = AirtableClientFactory(base_id=airtableBaseKey, api_key=airtableApiKey)
    at = atf.create('EmployeeDirectory')

    fields = {
   	    'slack_id': slackid,
   	    'kot_id': kotid
    }

    record = at.update(recordid, fields).get()