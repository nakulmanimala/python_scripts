import boto3
from config import conf
from Logger import Logger
import logging

log = Logger(logging)


class Authentication:
    def getSession(self, mode=None):
        try:
            if mode is 'profile':
                session = boto3.Session(
                    profile_name=conf['profile'], region_name=conf['region'])
                return session
            elif mode is 'sts':
                client = boto3.client('sts')
                response = client.assume_role(
                    RoleArn=conf['roleArn'], RoleSessionName='sess1',)
                session = boto3.Session(
                    aws_access_key_id=response['Credentials']['AccessKeyId'],
                    aws_secret_access_key=response['Credentials']['SecretAccessKey'],
                    aws_session_token=response['Credentials']['SessionToken'],
                    region_name=conf['region']
                )
                return session
            else:
                session = boto3.Session(region_name=conf['region'],)
                return session
        except Exception as e:
            log.error(e)

