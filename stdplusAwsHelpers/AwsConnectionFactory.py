import boto3
import json
import os

from botocore import configloader
from pprint import pprint
from stdplus import readfile
from stdplus import writefile

aws_config_dir = os.path.join(os.path.expanduser("~"), ".aws")

class AwsConnectionFactory:
    instance = None

    def __init__(self,credentials=None,profile='default',regionName=None):
        if None == credentials:
            credentialsFilename = self.getAwsMfaCredentialsFilename(profile)
            try:
                credentials = json.loads(readfile(credentialsFilename))['Credentials']
            except IOError:
                # print "WARN: IOError reading credentials file:{}".format(credentialsFilename)
                pass
            except ValueError:
                # print "WARN: ValueError reading credentials file:{}".format(credentialsFilename)
                pass
        self.setMfaCredentials(credentials,profile)
        self.regionName = regionName

    @staticmethod
    def resetInstance(credentials=None,profile='default', regionName=None):
        AwsConnectionFactory.instance = AwsConnectionFactory(credentials,profile,regionName)

    def getAwsMfaCredentialsFilename(self,profile='default'):
        credentials_file_name = 'mfa_credentials'
        if not 'default' == profile:
            credentials_file_name = "{}_{}".format(profile,'mfa_credentials')

        credentials_file  = os.path.join(aws_config_dir, credentials_file_name)
        return credentials_file

    def getAwsCredentialsFilename(self):
        return os.path.join(aws_config_dir,'credentials')

    def load_arn(self,profile):
        arn_file_name = 'mfa_device'
        if not profile == 'default':
            arn_file_name = "{}_{}".format(profile,arn_file_name)

        arn_file = os.path.join(aws_config_dir, arn_file_name)

        if os.access(arn_file,os.R_OK):
            return readfile(arn_file).strip()
        else:
            arn = self.load_arn_from_aws(profile)
            writefile(arn_file, arn)
            return arn

    def _strConfig(self,config):
        result = ""
        for section,settings in config.items():
            result += "[{}]\n".format(section)
            for key,value in settings.items():
                result += "{} = {}\n".format(key,value)
            result += "\n"
        return result

    def storeAwsMfa(self,credentials,profile):
        if not None == credentials:
            writefile(self.getAwsMfaCredentialsFilename(profile),json.dumps({'Credentials':credentials}))

    def storeAwsCredentials(self,credentials,profile):
        if credentials == None:
            return
        awsCredentials = configloader.raw_config_parse(self.getAwsCredentialsFilename(),False)
        if not profile in awsCredentials:
            awsCredentials[profile]={}
        awsCredentials[profile]['aws_access_key_id'] = credentials['AccessKeyId']
        awsCredentials[profile]['aws_secret_access_key'] = credentials['SecretAccessKey']
        if 'SessionToken' in credentials:
            awsCredentials[profile]['aws_session_token'] = credentials['SessionToken']
        awsCredentials = self._strConfig(awsCredentials)
        writefile(self.getAwsCredentialsFilename(),awsCredentials)

    def setMfaCredentials(self,credentials,profile='default'):
        self.storeAwsMfa(credentials,profile)
        self.storeAwsCredentials(credentials,profile + "-mfa");

        self.credentials = credentials
        self.session = None
        self.profile = profile

    def getProfile(self):
        return self.profile

    def getSession(self):
        if self.session == None:
            if self.credentials == None:
                # print("Getting session w/ credentials from env")
                self.session = boto3.session.Session(region_name=self.regionName)
            else:
                # print("Getting session w/ credentials:")
                # pprint(self.credentials)
                self.session = boto3.session.Session(aws_access_key_id=self.credentials['AccessKeyId'],
                                                     aws_secret_access_key=self.credentials['SecretAccessKey'],
                                                     aws_session_token=self.credentials['SessionToken'],
                                                     region_name=self.regionName)
                # print(self.session)
        # print "Session obtained"
        return self.session

    def getAsgClient(self):
        return self.getSession().client('autoscaling')

    def getAsgResource(self):
        return self.getSession().resource('autoscaling')

    def getCfResource(self):
        return self.getSession().resource('cloudformation')

    def getCfClient(self):
        return self.getSession().client('cloudformation')

    def getEc2Client(self):
        return self.getSession().client('ec2')

    def getEc2Resource(self):
        return self.getSession().resource('ec2')

    def getEksClient(self):
        return self.getSession().client('eks')

    def getIamClient(self):
        return self.getSession().client('iam')

    def getLogClient(self):
        return self.getSession().client('logs')

    def getRdsClient(self):
        return self.getSession().client('rds')

    def getS3Client(self):
        return self.getSession().client('s3')

    def getS3Resource(self):
        return self.getSession().resource('s3')


AwsConnectionFactory.instance = AwsConnectionFactory()
