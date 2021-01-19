import grpc
import time
import datetime

from utilities.IterableQueue import IterableQueue
from utilities.EventThread import EventThread
# from event_processors import *

from remote.HFRemote_pb2_grpc import *
from remote.TMSRemoteCommon_pb2 import *
from remote.HFRemoteRequests_pb2 import *
from remote.TMSRemoteRequests_pb2 import *
from remote.HFTrading_pb2 import *
from remote.HFTrading_pb2_grpc import *


def perform(target):
    ssl_credentials = grpc.ssl_channel_credentials(open('cert.pem', 'rb').read())
    channel = grpc.secure_channel(target, ssl_credentials)
    client = HFTradingStub(channel)

    client.login(LoginRequest(user='demohifreq', password=''))
    return client
