import re

from remote.TMSRemoteCommon_pb2 import *

from subscribtion import *
from targetLists import generate_unique_target_list_name
from utilities.Utilities import *

MANAGER_NAME = "Simulator-HiFreq Target Orders"


def add_targets(client):
    target_list_name = generate_unique_target_list_name()
    client.addTargetLists(AddTargetListsRequest(targetListName=[target_list_name]))
    client.addTargets(AddTargetsRequest(targetListName=target_list_name, fields=[{
        'stringFields': {'Instrument': 'IBM'},
        'numericFields': {'Side': Side_Buy, 'TgtQty': 100, 'TgtType': OrdType_Market}
    }]))
    wait_for_record({
        'stringFields': {'Instrument': 'IBM'},
        'numericFields': {'TgtQty': 100, 'Side': Side_Buy, 'TgtType': OrdType_Market}
    })

    client.addTargets(AddTargetsRequest(targetListName=target_list_name, fields=[{
        'stringFields': {'Instrument': 'IBM'},
        'numericFields': {'Side': Side_Buy, 'TgtQty': 200, 'TgtType': OrdType_Market}
    }, {
        'stringFields': {'Instrument': 'MSFT'},
        'numericFields': {'Side': Side_Sell, 'TgtQty': 300, 'TgtType': OrdType_Market}
    }]))
    wait_for_record({
        'stringFields': {'Instrument': 'IBM'},
        'numericFields': {'TgtQty': 200, 'Side': Side_Buy, 'TgtType': OrdType_Market}
    })
    wait_for_record({
        'stringFields': {'Instrument': 'MSFT'},
        'numericFields': {'TgtQty': 300, 'Side': Side_Sell, 'TgtType': OrdType_Market}
    })


def add_targets_with_bad_one(client):
    """
    Expect good targets to be added while a composite exception (with children) is raised for bad targets
    """
    target_list_name = generate_unique_target_list_name()
    client.addTargetLists(AddTargetListsRequest(targetListName=[target_list_name]))

    try:
        client.addTargets(AddTargetsRequest(targetListName=target_list_name, fields=[{
            'stringFields': {'Instrument': 'IBM'},
            'numericFields': {'Side': Side_Buy, 'TgtQty': 200, 'TgtType': OrdType_Market}
        }, {
            'stringFields': {'BadField': 'MSFT'},  # Bad field name
            'numericFields': {'Side': Side_Sell, 'TgtQty': -300, 'TgtType': OrdType_Market}
        }]))
        assert False, 'should not be here, exception is expected'
    except Exception as ex:
        if hasattr(ex, 'trailing_metadata'):
            metadata = dict(ex.trailing_metadata())
            child_exception_count = int(metadata.get("childexceptionscount", "0"))
            assert child_exception_count == 1
            error_message = metadata.get("childexceptionmessage_0")
            error_check("Creating new target is not correct. Next fields are unknown:\[BadField\].*", error_message)

    wait_for_record({
        'stringFields': {'Instrument': 'IBM'},
        'numericFields': {'TgtQty': 200, 'Side': Side_Buy, 'TgtType': OrdType_Market}
    })


def create_test_targets(client):
    target_list_name = generate_unique_target_list_name()
    client.addTargetLists(AddTargetListsRequest(targetListName=[target_list_name]))

    target_result = client.addTargets(AddTargetsRequest(targetListName=target_list_name, fields=[{
        'stringFields': {'Instrument': 'IBM'},
        'numericFields': {'Side': Side_Buy, 'TgtQty': 2000, 'TgtType': OrdType_Market, 'WaveSize': 100}
    }, {
        'stringFields': {'Instrument': 'MSFT', 'Symbol': 'MSFT', 'Currency': 'USD'},
        'numericFields': {'Side': Side_Sell, 'TgtQty': 3000, 'TgtType': OrdType_Market, 'WaveSize': 200}
    }]))

    target_ids = map(lambda x: x.targetId, target_result.result)
    return target_ids


def send_target_orders(client):
    target_ids = create_test_targets(client)

    order_id_result = client.sendTargetOrders(
        SendTargetsRequest(managerName=MANAGER_NAME, targetId=target_ids))

    order_ids = map(lambda x: x.orderId, order_id_result.result)

    wait_for_record(record_id=order_ids[0], expected={
        'stringFields': {'Instrument': 'IBM'},
        'numericFields': {'OrdType': OrdType_Market, 'Side': Side_Buy, 'OrdQty': 100}
    })
    wait_for_record(record_id=order_ids[1], expected={
        'stringFields': {'Instrument': 'MSFT'},
        'numericFields': {'OrdType': OrdType_Market, 'Side': Side_Sell, 'OrdQty': 200}
    })

def send_target_orders_one_message_for_all(client):
    """
    A single message with OrderQty applied to every target order, i.e. qty should be 300
    """
    target_ids = create_test_targets(client)

    order_id_result = client.sendTargetOrders(
        SendTargetsRequest(managerName=MANAGER_NAME, targetId=target_ids, message=[{'numericFields': {FIXTag_OrderQty: 300}}]))
    order_ids = map(lambda x: x.orderId, order_id_result.result)

    wait_for_record(record_id=order_ids[0], expected={
        'stringFields': {'Instrument': 'IBM'},
        'numericFields': {'OrdType': OrdType_Market, 'Side': Side_Buy, 'OrdQty': 300}
    })
    wait_for_record(record_id=order_ids[1], expected={
        'stringFields': {'Instrument': 'MSFT'},
        'numericFields': { 'OrdType': OrdType_Market, 'Side': Side_Sell, 'OrdQty': 300}
    })

def send_target_orders_message_for_each_order(client):
    """
    A message per target with OrderQty applied to the order.
    """
    target_ids = create_test_targets(client)

    order_id_result = client.sendTargetOrders(
        SendTargetsRequest(managerName=MANAGER_NAME, targetId=target_ids, message=[{'numericFields': {FIXTag_OrderQty: 400}},
                                                                                   {'numericFields': {FIXTag_OrderQty: 500}}]))
    order_ids = map(lambda x: x.orderId, order_id_result.result)

    wait_for_record(record_id=order_ids[0], expected={
        'stringFields': {'Instrument': 'IBM'},
        'numericFields': {'OrdType': OrdType_Market, 'Side': Side_Buy, 'OrdQty': 400}
    })
    wait_for_record(record_id=order_ids[1], expected={
        'stringFields': {'Instrument': 'MSFT'},
        'numericFields': { 'OrdType': OrdType_Market, 'Side': Side_Sell, 'OrdQty': 500}
    })

@exception_check('grpc._channel._Rendezvous', r'.*Wrong message count. Must be either 0 or 1 or a message per each target.*')
def send_target_orders_exception_messages_not_matching(client):
    """
    2 targets but incorrect 3 messages - exception is expected
    """
    target_ids = create_test_targets(client)

    order_id_result = client.sendTargetOrders(
        SendTargetsRequest(managerName=MANAGER_NAME, targetId=target_ids, message=[{'numericFields': {FIXTag_OrderQty: 400}},
                                                                                   {'numericFields': {FIXTag_OrderQty: 500}},
                                                                                   {'numericFields': {FIXTag_OrderQty: 600}},
                                                                                   ]))
