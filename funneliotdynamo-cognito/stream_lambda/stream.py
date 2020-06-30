import os
import json
import base64
import decimal
import logging
import boto3
from boto3.dynamodb.types import TypeDeserializer

deserializer = TypeDeserializer()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# メールの送受信先は、template.yamlで定義。環境変数で受け取る
SRC_MAIL = os.environ['MAIL_ADDRESS']
DST_MAIL = os.environ['MAIL_ADDRESS']
# リージョンはオレゴン
REGION = "us-west-2"

def send_email(source, to, subject, body):
    """
    SESでメールを送信する
    """
    client = boto3.client('ses', region_name=REGION)

    response = client.send_email(
        Source=source,
        Destination={
            'ToAddresses': [
                to,
            ]
        },
        Message={
            'Subject': {
                'Data': subject,
            },
            'Body': {
                'Text': {
                    'Data': body,
                },
            }
        }
    )
    
    return response

# AWSの開発者ガイドに書かれていたDecimal型から数値に変換するHelper class
# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

def stream_request_lambda_handler(event, context):
    """
    DynamoDB Streamに登録する関数
    """
    logger.debug('## ENVIRONMENT VARIABLES')
    logger.debug(os.environ)
    logger.debug('## EVENT')
    logger.debug(event) 
    # 複数のデータがRecoresに入る
    recos = event['Records']
    for reco in recos:
        # 1レコードごとに処理
        if reco["eventName"] == "INSERT":
            logger.info("-- insert --")
            newimage = reco['dynamodb']['NewImage']
            # SORACOM FunnelはpayloadsにSIMからの情報を入れる
            payload = newimage['payloads']
            # boto3のTypeDeserializerでpythonの型に変換。(辞書型とかの入れ子になっていると上手く動かない)
            ret_dict = deserializer.deserialize(payload)
            ret_srt = json.dumps(ret_dict, cls=DecimalEncoder)
            logger.debug("NewImage:" + ret_srt)
            #print("NewImage:" + ret_srt)
            if ret_dict["type"] == 1:
                tmp_str = "gps_multiunitのボタンが押されました。\n" \
                    + "緯度: " + str(ret_dict["lat"]) + "\n" \
                    + "経度: " + str(ret_dict["lon"]) + "\n" \
                    + "https://www.google.com/maps?q="+str(ret_dict["lat"])+","+str(ret_dict["lon"])
                send_email(SRC_MAIL, DST_MAIL, "gps_multiunitのボタン", tmp_str)
                logger.info("send mail")

    return {"result": "OK"}

if __name__ == '__main__':
    # 確認用プログラム
    print("-- sart --")
    event = {
        'Records': [
            {'eventID': '3f2xxxxxxxxxxxxxxxxxxx2',
             'eventName': 'INSERT',
             'eventVersion': '1.1',
             'eventSource': 'aws:dynamodb',
             'awsRegion': 'us-west-2',
             'dynamodb': {'ApproximateCreationDateTime': 1592914854.0,
               'Keys': {'imsi': {'S': '440IMSI_NUM'}, 'timestamp': {'N': '1592914852899'}},
               'NewImage': {'payloads': {'M': {'rs': {'N': '4'},
                   'temp': {'N': '33.3'},
                   'bat': {'N': '3'},
                   'humi': {'N': '48.7'},
                   'x': {'N': '0'},
                   'y': {'N': '0'},
                   'lon': {'N': '135.12312'},
                   'z': {'N': '-1024'},
                   'type': {'N': '1'},
                   'lat': {'N': '35.12312'}}},
                 'sourceProtocol': {'S': 'udp'},
                 'destination': {'M': {'resourceUrl': {'S': 'https://AWS-IoTCore-URL.iot.us-west-2.amazonaws.com/gpsmulti/#{imsi}'}, 'provider': {'S': 'aws'}, 'service': {'S': 'aws-iot'}}}, 'credentialsId': {'S': 'IAM_soracom-user'}, 'imsi': {'S': '440IMSI_NUM'}, 'TTL': {'N': '1655986852'}, 'operatorId': {'S': 'OP00SORACOM_OP_NUM'}, 'timestamp': {'N': '1592914852899'}}, 'SequenceNumber': '12345000000000123456', 'SizeBytes': 348, 'StreamViewType': 'NEW_IMAGE'}, 'eventSourceARN': 'arn:aws:dynamodb:us-west-2:12345678:table/xxxxxxxx/stream/2020-06-23T12:14:52.665'}]}

    stream_request_lambda_handler(event, None)