from Authentication import Authentication
from Redis import Redis
from config import conf
import argparse
import time
import logging
from Logger import Logger

log = Logger(logging)


def main():
    # Intialising argparser
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--action", help="start or stop are the options.", type=str)
    args = parser.parse_args()
    # Authenticating
    auth = Authentication()
    sess = auth.getSession(conf['mode'])
    # Creating object of redis
    r = Redis(sess)

    # Options to be executed!
    if(args.action == "start"):
        r.createReplicationGroup()
    elif(args.action == "stop"):
        r.createRedisSnapshot()
        r.isSnapshotCompleted()
        r.deleteReplicationGroup()
        r.deleteOlderSnapshots()
    else:
        print(f'Please enter a valid option, either start|stop are only valid')
        log.error("Please enter a valid option, either start|stop are only valid")


# Entry point
if __name__ == '__main__':
    main()

