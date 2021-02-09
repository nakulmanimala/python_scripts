from config import conf
import time
import datetime
import sys
from Logger import Logger
import logging

log = Logger(logging)


class Redis:

    def __init__(self, sess):
        self.sess = sess
        self.client = self.sess.client('elasticache')
        self.latestSnap = ''

    def createRedisSnapshot(self):
        try:
            resp = self.client.create_snapshot(
                ReplicationGroupId=conf['repGroupId'],
                CacheClusterId=conf['clusterId'],
                SnapshotName=conf['snapName'] + '-' +
                time.strftime("%Y-%m-%d-%H%M%S", time.localtime()),
            )
            # print(f'status %s' % resp['Snapshot']['SnapshotStatus'])
            log.info("Status of snapshot: " +
                     resp['Snapshot']['SnapshotStatus'])
        except Exception as e:
            log.error(e)
            sys.exit()

    def getLatestSnapshots(self):
        try:
            snap_dict = {}
            snap_array = []
            resp = self.client.describe_snapshots(
                # ReplicationGroupId=conf['repGroupId'],
                CacheClusterId=conf['clusterId'],
            )
            for i in resp['Snapshots']:
                for j in i['NodeSnapshots']:
                    snap_dict[j['SnapshotCreateTime']] = i['SnapshotName']
            snap_array = snap_dict.keys()
            return snap_dict.get(max(snap_array))
        except Exception as e:
            log.error(e)
            sys.exit()

    def deleteOlderSnapshots(self):
        try:
            snap_dict = {}
            snap_array = []
            resp = self.client.describe_snapshots(
                CacheClusterId=conf['clusterId'],
            )
            for i in resp['Snapshots']:
                for j in i['NodeSnapshots']:
                    snap_dict[j['SnapshotCreateTime']] = i['SnapshotName']
            snap_array = snap_dict.keys()
            if(len(snap_array) > 7):
                snap_list = list(snap_array)
                for _s in range(0, 7):
                    snap_list.remove(max(snap_list))
                for rem in snap_list:
                    # print(f'Deleting snapshot %s' % snap_dict[rem])
                    log.warn("Deleting snapshot: " + snap_dict[rem])
                    deleteResp = self.client.delete_snapshot(
                        SnapshotName=snap_dict[rem]
                    )
                    log.info(deleteResp)
            else:
                # print(f'Nothing to be deleted...!')
                log.info("Nothing to be deleted!!!")
        except Exception as e:
            log.error(e)
            sys.exit()

    def isSnapshotCompleted(self):
        clusterStatus = ''
        lp = 0
        try:
            while clusterStatus != 'available':
                resp = self.client.describe_cache_clusters(
                    CacheClusterId=conf['clusterId'],

                )
                for status in resp['CacheClusters']:
                    clusterStatus = status['CacheClusterStatus']
                k = 120
                sec = 1
                while k > 0:
                    time.sleep(1)
                    log.info("waiting... " + str(sec+(lp*120)) +
                             " seconds elapsed!")
                    sec = sec + 1
                    k = k - 1
                lp = lp + 1
            log.info("Snapshotting completed!!!!")
        except Exception as e:
            log.error(e)

    def createReplicationGroup(self):
        try:
            resp = self.client.create_replication_group(
                ReplicationGroupId=conf['repGroupId'],
                ReplicationGroupDescription=conf['repGroupId'],
                AutomaticFailoverEnabled=False,
                NumCacheClusters=1,
                CacheNodeType=conf['cacheNodeType'],
                Engine=conf['engine'],
                EngineVersion=conf['engineVersion'],
                CacheParameterGroupName=conf['parameterGroup'],
                CacheSubnetGroupName=conf['subnetGroup'],
                SecurityGroupIds=conf['securityGroups'],
                Tags=conf['tags'],
                SnapshotName=self.getLatestSnapshots(),
                Port=6379
            )
            log.info(resp)
        except Exception as e:
            log.error(e)

    def deleteReplicationGroup(self):
        try:
            resp = self.client.delete_replication_group(
                ReplicationGroupId=conf['repGroupId']
            )
            log.info(resp)
        except Exception as e:
            log.error(e)

