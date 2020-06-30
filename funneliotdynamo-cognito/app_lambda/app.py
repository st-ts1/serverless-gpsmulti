import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
import base64
import decimal
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# import requests

# AWSの開発者ガイドに書かれていたDecimalから数値に変換するHelper class
# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

def lambda_handler(event, context):
    """
    API Gateway用ハンドラー
    
    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    logger.debug('## ENVIRONMENT VARIABLES')
    logger.debug(os.environ)
    logger.debug('## EVENT')
    logger.debug(event)
    #logger.debug('## CONTEXT')
    #logger.debug(context)

    # eventのqueryStringParametersがGETしたパラメータ
    q_string_p = event["queryStringParameters"]
    # 想定文字列
    # curl "https://XXXXXXXXXX.us-west-2.amazonaws.com/v1/data?imsi=440IMSI_NUM&from=123&to=456&sort=desc&limit=3" -H "Authorization:1pass12345!"

    # パラメータ解析
    if q_string_p == None:
        return {
            "statusCode": 400,
            "body": json.dumps({
            "message": "imsi needed",
            }),
        }
    if "imsi" not in q_string_p:
        return {
            "statusCode": 400,
            "body": json.dumps({
            "message": "imsi needed",
            }),
        }
    taget_imsi = q_string_p["imsi"]
    from_oldermepoch = None
    if "from" in q_string_p:
        from_oldermepoch = int(q_string_p["from"])
    to_newermepoch = None
    if "to" in q_string_p:
        to_newermepoch = int(q_string_p["to"])
    sort = "desc"
    if "sort" in q_string_p:
        sort = q_string_p["sort"]
    limit = 10
    if "limit" in q_string_p:
        limit = int(q_string_p["limit"])
    # データ取得
    dynamo = boto3.resource('dynamodb').Table(os.environ['TABLE_NAME'])
    res = getData(dynamo, taget_imsi, from_oldermepoch, to_newermepoch, sort, limit)
    ret_dict = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(res, cls=DecimalEncoder)
    }
    return ret_dict
    
def getData(dynamo, imsi:str, from_oldermepoch:int=None, to_newermepoch:int=None, sort:str="desc", limit:int=10):
    """
    指定されたデータを取得
    """
    sortbool:bool = False # 昇順か降順か(DynamoDBのデフォルトはtrue=昇順)
    if sort == "desc":
        sortbool= False # 降順
    elif sort == "asc":
        sortbool= True # 昇順
    logger.debug("getData("+imsi+", "+str(from_oldermepoch)+", "+str(to_newermepoch)+","+sort+", "+str(limit)+")")
    if from_oldermepoch == None and to_newermepoch == None:
        tmp_q = dynamo.query( KeyConditionExpression = Key('imsi').eq(imsi),
        ScanIndexForward = sortbool,
        Limit= limit
        )
    elif from_oldermepoch != None and to_newermepoch == None:
        tmp_q = dynamo.query(
        KeyConditionExpression = Key('imsi').eq(imsi) & Key('timestamp').gte(from_oldermepoch),
        ScanIndexForward = sortbool,
        Limit= limit
        )
    elif from_oldermepoch == None and to_newermepoch != None:
        tmp_q = dynamo.query(
        KeyConditionExpression = Key('imsi').eq(imsi) & Key('timestamp').lte(to_newermepoch),
        ScanIndexForward = sortbool,
        Limit= limit
        )
    elif from_oldermepoch != None and to_newermepoch != None:
        tmp_q = dynamo.query(
        KeyConditionExpression = Key('imsi').eq(imsi) & Key('timestamp').between(from_oldermepoch, to_newermepoch),
        ScanIndexForward = sortbool,
        Limit= limit
        )
    # queryした結果のItemsに本当の結果が入っている
    #res = tmp_q["Items"]
    #return res
    return tmp_q

if __name__ == '__main__':
    print("-- sart --")
    dynamo = boto3.resource('dynamodb').Table(os.environ['TABLE_NAME'])
    #res = getData(dynamo, "440IMSI_NUM")
    res = getData(dynamo, "440IMSI_NUM", 1590750073000, 1590759773000, "desc", 3)
    print(res)
    print("---")
    ret_dict = {
        "statusCode": 200,
        "body": json.dumps(res, cls=DecimalEncoder)
    }
    print(ret_dict)