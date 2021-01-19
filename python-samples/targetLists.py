import time

from remote.HFRemoteRequests_pb2 import *
from remote.TMSRemoteCommon_pb2 import *
from utilities.Utilities import exception_check
from subscribtion import *

unique_identifier = time.time()

MANAGER_NAME = "Simulator-HiFreq Target Orders"

def generate_unique_target_list_name():
    global unique_identifier
    unique_identifier = unique_identifier + 1
    return "TargetList_" + str(unique_identifier)


def add_target_lists_empty_fields(client):
    target_list_name = generate_unique_target_list_name()
    client.addTargetLists(
        AddTargetListsRequest(targetListName=[target_list_name])
    )
    wait_for_record({
        'stringFields': {'Name': target_list_name},
        'numericFields': {}})

    target_list_name_1 = generate_unique_target_list_name()
    target_list_name_2 = generate_unique_target_list_name()
    client.addTargetLists(
        AddTargetListsRequest(targetListName=[target_list_name_1, target_list_name_2])
    )
    wait_for_record({
        'stringFields': {'Name': target_list_name_1},
        'numericFields': {}})
    wait_for_record({
        'stringFields': {'Name': target_list_name_2},
        'numericFields': {}})


def add_target_lists_same_fields_for_all(client):
    target_list_name_1 = generate_unique_target_list_name()
    target_list_name_2 = generate_unique_target_list_name()
    client.addTargetLists(
        AddTargetListsRequest(targetListName=[target_list_name_1, target_list_name_2],
                              fields=[{
                                  'stringFields': {'CustomStr1': 'MyString1'},
                                  'numericFields': {'CustomNum1': 11},
                              }
                              ])
    )
    wait_for_record({
        'stringFields': {'Name': target_list_name_1, 'CustomStr1': 'MyString1'},
        'numericFields': {'CustomNum1' : 11}})
    wait_for_record({
        'stringFields': {'Name': target_list_name_2, 'CustomStr1': 'MyString1'},
        'numericFields': {'CustomNum1' : 11}})


def add_target_lists_with_fields_per_list(client):
    target_list_name_1 = generate_unique_target_list_name()
    target_list_name_2 = generate_unique_target_list_name()
    client.addTargetLists(
        AddTargetListsRequest(targetListName=[target_list_name_1, target_list_name_2],
                              fields=[
                                  {
                                      'stringFields': {'CustomStr1': 'MyString1'},
                                      'numericFields': {'CustomNum1': 11},
                                  },
                                  {
                                      'stringFields': {'CustomStr1': 'MyString2'},
                                      'numericFields': {'CustomNum1': 22},
                                  }
                              ])
    )
    wait_for_record({
        'stringFields': {'Name': target_list_name_1, 'CustomStr1': 'MyString1'},
        'numericFields': {'CustomNum1': 11}})
    wait_for_record({
        'stringFields': {'Name': target_list_name_2, 'CustomStr1': 'MyString2'},
        'numericFields': {'CustomNum1': 22}})


@exception_check('grpc._channel._Rendezvous', r'Number of target list names and fields should be same')
def add_target_lists_wrong_params(client):
    target_list_name_1 = generate_unique_target_list_name()
    target_list_name_2 = generate_unique_target_list_name()
    target_list_name_3 = generate_unique_target_list_name()
    client.addTargetLists(
        AddTargetListsRequest(targetListName=[target_list_name_1, target_list_name_2, target_list_name_3],
                              fields=[{
                                  'stringFields': {'CustomStr1': 'MyString1'},
                                  'numericFields': {'CustomNum1': 11},
                              }, {
                                  'stringFields': {'CustomStr1': 'MyString2'},
                                  'numericFields': {'CustomNum1': 22},
                              }
                              ])
    )


def send_target_list_orders(client):
    """
    A single message with OrderQty applied to every target order, i.e. qty should be 300
    """
    target_list_name = generate_unique_target_list_name()
    client.addTargetLists(AddTargetListsRequest(targetListName=[target_list_name]))

    client.addTargets(AddTargetsRequest(targetListName=target_list_name, fields=[{
        'stringFields': {'Instrument': 'IBM'},
        'numericFields': {'Side': Side_Buy, 'TgtQty': 2000, 'TgtType': OrdType_Market, 'WaveSize': 100}
    }, {
        'stringFields': {'Instrument': 'MSFT', 'Symbol': 'MSFT', 'Currency': 'USD'},
        'numericFields': {'Side': Side_Sell, 'TgtQty': 3000, 'TgtType': OrdType_Market, 'WaveSize': 200}
    }]))


    # First sending without a message
    client.sendTargetListOrders(
        SendTargetListOrdersRequest(managerName=MANAGER_NAME, targetListName=[target_list_name]))

    wait_for_record({
        'stringFields': {'Instrument': 'IBM'},
        'numericFields': {'OrdType': OrdType_Market, 'Side': Side_Buy, 'OrdQty': 100}
    })
    wait_for_record({
        'stringFields': {'Instrument': 'MSFT'},
        'numericFields': { 'OrdType': OrdType_Market, 'Side': Side_Sell, 'OrdQty': 200}
    })

    # Now the same with message specifying order qty
    client.sendTargetListOrders(
        SendTargetListOrdersRequest(managerName=MANAGER_NAME, targetListName=[target_list_name],
                                    message={'numericFields': {FIXTag_OrderQty: 300}}))

    wait_for_record({
        'stringFields': {'Instrument': 'IBM'},
        'numericFields': {'OrdType': OrdType_Market, 'Side': Side_Buy, 'OrdQty': 300}
    })
    wait_for_record({
        'stringFields': {'Instrument': 'MSFT'},
        'numericFields': { 'OrdType': OrdType_Market, 'Side': Side_Sell, 'OrdQty': 300}
    })
