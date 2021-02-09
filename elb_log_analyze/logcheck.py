import os
import boto3
import sys
import logging
import re
import datetime
import botocore
import gzip
from config import config
from datetime import timedelta
from os.path import basename

line_count = 0
client_s3 = boto3.client('s3')
client_elb = boto3.client('elb')
client_elb_v2 = boto3.client('elbv2')
resource_s3 = boto3.resource('s3')

log_file = config['log_file']
log_level = config['log_level']
formatter = config['formatter']
d_location = config['log_d_location']
account = config['account']
region = config['region']

logging.basicConfig(filename=log_file, level=log_level, format=formatter)

type = sys.argv[1]
dat = sys.argv[2]
tim = sys.argv[3]
elb_name = sys.argv[4]
res_code = sys.argv[5]
alb_arn = sys.argv[4]

yer = dat.split("-")[2]
mnth = dat.split("-")[1]
dy = dat.split("-")[0]
dattm = sys.argv[2] + " " + sys.argv[3]

d = datetime.datetime.strptime(dattm, '%d-%m-%Y %X')
#The dplus and dminus are the time difference to collect the modified files in time range
# The dplus_1 and dminus_1 are the time difference to get the records in the s3 log files
# the dplus_1 shouldnot be grater than the value of dplus
dplus = d + timedelta(hours=12)
dminus = d - timedelta(hours=12)

dplus_1 = d + timedelta(hours=11)
dminus_1 = d - timedelta(hours=11)
#dplus_1 = d + timedelta(minutes=10)
#dminus_1 = d - timedelta(minutes=10)


def download_object(log_bucket_name, obj_path, dest_path):
    # print "Downloading Object - " + obj_path

    try:
        resource_s3.Bucket(log_bucket_name).download_file(obj_path, dest_path)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise


def main():
    print "Checking log between " +str(dplus_1)+ " and " +str(dminus_1) +" UTC"
    if type == "ELB":
        print "Checking ELB Details"
        if elb_name == "null":
            print "No elb name provided"
            exit(0)
        try:
            response = client_elb.describe_load_balancer_attributes(LoadBalancerName=elb_name)
        except botocore.exceptions.ClientError as e:
            print "error describing load balancer - Give the currect ELB name"
            print "%s" % (e)
            exit(0)
        if response['LoadBalancerAttributes']['AccessLog']['Enabled'] == True:
		log_bucket_name = response['LoadBalancerAttributes']['AccessLog']['S3BucketName']
		if response['LoadBalancerAttributes']['AccessLog']['S3BucketName'] == "":
			bucket_prefix = response['LoadBalancerAttributes']['AccessLog']['S3BucketPrefix']
		else:
	    		bucket_prefix = response['LoadBalancerAttributes']['AccessLog']['S3BucketPrefix']+"/"
        else:
		print "Elb is not enabled with access log"
            	exit(0)

        prfx_elb = bucket_prefix + "AWSLogs/" + account + "/elasticloadbalancing/" + region + "/" + yer + "/" + mnth + "/" + dy + "/" + account + "_elasticloadbalancing_" + region + "_" + elb_name + "_" + yer + mnth + dy

        response = client_s3.list_objects_v2(Bucket=log_bucket_name, MaxKeys=1000, Prefix=prfx_elb)
        dtm = str(datetime.datetime.now().strftime('%Y-%m-%d--%X')) + ".txt"
        f = open(d_location + "output_log_" + elb_name + dtm, "w+")

        conents = response['Contents']
        for line in conents:
            base_name = (basename(line['Key']))
            if line['LastModified'].strftime('%Y-%m-%d %X') > datetime.date.strftime(dminus, '%Y-%m-%d %X') and line[
                'LastModified'].strftime('%Y-%m-%d %X') < datetime.date.strftime(dplus, '%Y-%m-%d %X'):
                download_object(log_bucket_name, line['Key'], d_location + base_name)
                with open(d_location + base_name) as data_file:
                    for file_line in data_file:
                        if res_code == "5xx":
                            p = re.compile('^5\d\d$')
                        elif res_code == "4xx":
                            p = re.compile('^4\d\d$')
                        elif res_code == "3xx":
                            p = re.compile('^3\d\d$')
                        else:
                            print ("Unknown code error code to find")
                            exit(0)
                        m = p.match(file_line.split()[7])
                        n = p.match(file_line.split()[8])
                        if m or n:
                            #print file_line
                            dtm_in_file = datetime.datetime.strptime(file_line.split()[0], '%Y-%m-%dT%X.%fZ')
                            dtm_in_file_frmtd = dtm_in_file.strftime('%Y-%m-%d %X')
                            # print "--" + dtm_in_file_frmtd
                            if dtm_in_file_frmtd > datetime.date.strftime(dminus_1,
                                                                          '%Y-%m-%d %X') and dtm_in_file_frmtd < datetime.date.strftime(
                                    dplus_1, '%Y-%m-%d %X'):
                                f.write(file_line + "\n")
                                print file_line
                try:
                    os.remove(d_location + base_name)
                except OSError:
                    print "Unable to delete downloaded file"
        f.close()  # line_count = line_count + 1
        with open(d_location + "output_log_" + elb_name + dtm, 'rb') as data:
            client_s3.upload_fileobj(data, 'aem-data-temp', "output_log_" + elb_name + dtm)
        print "file has been uploaded to S3. -- S3://aem-data-temp/" + "output_log_" + elb_name + dtm
        try:
            os.remove(d_location + "output_log_" + elb_name + dtm)
        except OSError:
            print "Unable to delete downloaded file"


    elif type == "ALB":
        print "Checking ALB details"
        if alb_arn == "null":
            print "No ALB ARN provided"
            exit(0)
        try:
            response = client_elb_v2.describe_load_balancer_attributes(LoadBalancerArn=alb_arn)
        except botocore.exceptions.ClientError as e:
            print "error describing load balancer -- Give the currect ALB ARN"
            print "%s" % (e)
            exit(0)
            # print response
        for res in response['Attributes']:
            if res['Key'] == "access_logs.s3.enabled" and res['Value'] == 'false':
                print "Access Log not enabled"
                exit(0)

            elif res['Key'] == "access_logs.s3.enabled" and res['Value'] == 'true':
                for i in response['Attributes']:
                    if i['Key'] == "access_logs.s3.bucket":
                        log_bucket_name = i['Value']
                    if i['Key'] == "access_logs.s3.prefix":
			if i['Value'] == "":
				bucket_prefix = i['Value']
			else:
                        	bucket_prefix = i['Value']+"/"
                        # print log_bucket_name
                        # print bucket_prefix
                alb_id = alb_arn.split("/")[3]
                alb_name = alb_arn.split("/")[2]

                prfx_alb = bucket_prefix + "AWSLogs/" + account + "/elasticloadbalancing/" + region + "/" + yer + "/" + mnth + "/" + dy + "/" + account + "_elasticloadbalancing_" + region + "_app." + alb_name + "." + alb_id + "_" + yer + mnth + dy
                #print prfx_alb
                response = client_s3.list_objects_v2(Bucket=log_bucket_name, MaxKeys=1000, Prefix=prfx_alb)
                #print response
                dtm = str(datetime.datetime.now().strftime('%Y-%m-%d--%X')) + ".txt"
                f = open(d_location + "output_log_" + alb_name + dtm, "w+")
                conents = response['Contents']
                for line in conents:
                    base_name = (basename(line['Key']))
                    if line['LastModified'].strftime('%Y-%m-%d %X') > datetime.date.strftime(dminus, '%Y-%m-%d %X') and \
                                    line['LastModified'].strftime('%Y-%m-%d %X') < datetime.date.strftime(dplus,
                                                                                                          '%Y-%m-%d %X'):
                        download_object(log_bucket_name, line['Key'], d_location + base_name)
                        with gzip.open(d_location + base_name, 'r') as f1:
                            file_content = f1.read()
                            for file_line in file_content.splitlines():
                                if res_code == "5xx":
                                    p = re.compile('^5\d\d$')
                                elif res_code == "4xx":
                                    p = re.compile('^4\d\d$')
                                elif res_code == "3xx":
                                    p = re.compile('^3\d\d$')
                                else:
                                    print ("Unknown error code to check")
                                    exit(0)
                                m = p.match(file_line.split()[8])
                                n = p.match(file_line.split()[9])
                                if m or n:
                                    #print file_line.split()[1]
                                    dtm_in_file = datetime.datetime.strptime(file_line.split()[1], '%Y-%m-%dT%X.%fZ')
                                    dtm_in_file_frmtd = dtm_in_file.strftime('%Y-%m-%d %X')
                                    #print "--" + dtm_in_file_frmtd
                                    if dtm_in_file_frmtd > datetime.date.strftime(dminus_1, '%Y-%m-%d %X') and dtm_in_file_frmtd < datetime.date.strftime(dplus_1, '%Y-%m-%d %X'):
                                        f.write(file_line + "\n")
                                        #Uncomment below to get output in rundeck UI
					#print file_line
                                        # line_count=line_count+1
                        try:
                            os.remove(d_location + base_name)
                        except OSError:
                            print "Unable to delete downloaded file"
                f.close()
                with open(d_location + "output_log_" + alb_name + dtm, 'rb') as data:
                    client_s3.upload_fileobj(data, 'aem-data-temp', "output_log_" + alb_name + dtm)
                print "file has been uploaded to S3. -- S3://aem-data-temp/" + "output_log_" + alb_name + dtm
                try:
                    os.remove(d_location + "output_log_" + alb_name + dtm)
                except OSError:
                    print "Unable to delete downloaded file"

                    # if response['LoadBalancerAttributes']['AccessLog']['Enabled'] == True:
                    #    print response
                    #    log_bucket_name= response['LoadBalancerAttributes']['AccessLog']['S3BucketName']
                    #    bucket_prefix= response['LoadBalancerAttributes']['AccessLog']['S3BucketPrefix']
                    # else:
                    #    print "Elb is not enabled with access log"
                    #    exit(1)
                    # print log_bucket_name
                    # print bucket_prefix

    else:
        print "Invalid type"


if __name__ == '__main__':
    main()
