conf = {
    "mode": 'profile',  # use either "profile,sts or None"
    "region": "eu-west-1",
    "profile": "",
    "roleArn": "xxxxx",  # if you are using STS, then this should be given with a valid ARN

    # Redis conf
    "repGroupId": "",
    "clusterId": "",
    "snapName": "",
    "azMode": "",
    "numCacheNodes": 1,
    "cacheNodeType": "cache.r3.xlarge",
    "engine": "redis",
    "engineVersion": "5.0.3",
    "parameterGroup": "",
    "subnetGroup": "",
    "securityGroups": [""],
    "tags": [{'Key': 'PROJECT', 'Value': 'XXXXXXX'}],

    # Log location
    "logLocation": "/tmp/log.log"

}

