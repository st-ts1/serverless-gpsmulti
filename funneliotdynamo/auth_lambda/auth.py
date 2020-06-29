import os
import json
import base64
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def auth_request_lambda_handler(event, context):
    # 参考: https://dev.classmethod.jp/server-side/serverless/lambda-authorizer/
    logger.debug('## ENVIRONMENT VARIABLES')
    logger.debug(os.environ)
    logger.debug('## EVENT')
    logger.debug(event) 
    token = event["headers"]["Authorization"]
    logger.info('## token='+str(token) )
    if token == "pass12345!":
        logger.info('## sucess' )
        # 後続処理へのデータの引き渡し
        myaddisonalinfo = {
          "id": 12345,
          "hoge": "foo"
        }
        tmp_str = json.dumps(myaddisonalinfo)
        base64_context = base64.b64encode(tmp_str.encode('utf8'))
        return {
            "principalId" : token,
            "policyDocument" : {
                "Version" : "2012-10-17",
                "Statement" : [
                    {
                        "Action": "*",
                        "Effect": "Allow",
                        "Resource": "arn:aws:execute-api:*:*:*/*"  
                    }
                ]
            },
            'context': {
                'additional_info': base64_context.decode('utf-8')
            }
        }
    # パスワード不一致時はNG
    return {
        "principalId" : 2,
        "policyDocument" : {
            "Version" : "2012-10-17",
            "Statement" : [
                {
                    "Action": "*",
                    "Effect": "Deny",
                    "Resource": "arn:aws:execute-api:*:*:*/*"  
                }
            ]
        }
    }
