import time
import re

from remote.HFRemoteRequests_pb2 import *
from remote.TMSRemoteCommon_pb2 import *
from utilities.Utilities import *
from subscribtion import *

MANAGER_NAME = "Simulator-HiFreq"


def send_single_order(client):
    client.sendOrders(
        SendOrdersRequest(
            managerName=MANAGER_NAME,
            message=[{
                'stringFields': {FIXTag_Instrument: 'MSFT', FIXTag_Symbol: 'MSFT', FIXTag_Text: 'NOFILL'},
                'numericFields': {FIXTag_OrderQty: 400, FIXTag_OrdType: OrdType_Limit, FIXTag_Price: 100, FIXTag_Side: Side_Buy,
                                  FIXTag_HandlInst: HandlInst_AutomatedExecutionOrderPublicBrokerInterventionOk}}
            ]
        ))
    wait_for_record({
        'stringFields': {'Instrument': 'MSFT', 'Text': 'NOFILL'},
        'numericFields': {'OrdQty': 400, 'OrdType': OrdType_Limit}})


def send_multiple_orders(client):
    order_id_result = client.sendOrders(
        SendOrdersRequest(
            managerName=MANAGER_NAME,
            message=[
                {'stringFields': {FIXTag_Instrument: 'MSFT', FIXTag_Symbol: 'MSFT', FIXTag_Text: 'NOFILL'},
                 'numericFields': {FIXTag_OrderQty: 300, FIXTag_OrdType: OrdType_Limit, FIXTag_Price: 100, FIXTag_Side: Side_Buy,
                                   FIXTag_HandlInst: HandlInst_AutomatedExecutionOrderPublicBrokerInterventionOk}},
                {'stringFields': {FIXTag_Instrument: 'IBM', FIXTag_Symbol: 'IBM', FIXTag_Text: 'NOFILL'},
                 'numericFields': {FIXTag_OrderQty: 500, FIXTag_OrdType: OrdType_Limit, FIXTag_Price: 100, FIXTag_Side: Side_Buy,
                                   FIXTag_HandlInst: HandlInst_AutomatedExecutionOrderPublicBrokerInterventionOk}}
            ]
        ))
    wait_for_record({
        'stringFields': {'Instrument': 'MSFT', 'Text': 'NOFILL'},
        'numericFields': {'OrdQty': 300, 'OrdType': OrdType_Limit}})
    wait_for_record({
        'stringFields': {'Instrument': 'IBM', 'Text': 'NOFILL'},
        'numericFields': {'OrdQty': 500, 'OrdType': OrdType_Limit}})

    order_ids = map(lambda x: x.orderId, order_id_result.result)

    return order_ids


def send_empty(client):
    # Empty messages allowed, nothing is sent, no exception
    client.sendOrders(
        SendOrdersRequest(
            managerName=MANAGER_NAME
        ))


@exception_check('grpc._channel._Rendezvous', r'.*Unknown.*order manager "BadManager".*')
def exception_wrong_order_manager(client):
    client.sendOrders(
        SendOrdersRequest(
            managerName="BadManager",
            message=[{
                'stringFields': {FIXTag_Instrument: 'MSFT', FIXTag_Symbol: 'MSFT', FIXTag_Text: 'NOFILL'},
                'numericFields': {FIXTag_OrderQty: 300, FIXTag_OrdType: OrdType_Limit, FIXTag_Price: 100, FIXTag_Side: Side_Buy,
                                  FIXTag_HandlInst: HandlInst_AutomatedExecutionOrderPublicBrokerInterventionOk}}
            ]
        ))


@exception_check('grpc._channel._Rendezvous', r'.*Unknown.*order manager "".*')
def exception_no_manager(client):
    # manager name is not specified
    client.sendOrders(
        SendOrdersRequest(
            message=[{
                'stringFields': {FIXTag_Instrument: 'MSFT', FIXTag_Symbol: 'MSFT', FIXTag_Text: 'NOFILL'},
                'numericFields': {FIXTag_OrderQty: 300, FIXTag_OrdType: OrdType_Limit, FIXTag_Price: 100, FIXTag_Side: Side_Buy,
                                  FIXTag_HandlInst: HandlInst_AutomatedExecutionOrderPublicBrokerInterventionOk}}
            ]
        ))


def error_wrong_message(client):
    # message does not have required fields like FIXTag_Instrument or FIXTag_OrderQty
    order_id_result = client.sendOrders(SendOrdersRequest(managerName=MANAGER_NAME, message=[
        {'stringFields': {FIXTag_Text: 'NOFILL'}, 'numericFields': {FIXTag_OrdType: OrdType_Limit, FIXTag_Price: 100, FIXTag_Side: Side_Buy}}]))

    assert "error" == order_id_result.result[0].WhichOneof("result")
    assert order_id_result.result[0].orderId == 0
    error_check("Cannot send a request message with empty or 0 order quantity.*", order_id_result.result[0].error)


def send_and_get_orders(client):
    order_results = client.sendAndGetOrders(SendOrdersRequest(managerName=MANAGER_NAME, message=[
        {'stringFields': {FIXTag_Instrument: 'MSFT', FIXTag_Symbol: 'MSFT', FIXTag_Text: 'NOFILL'},
         'numericFields': {FIXTag_OrderQty: 300, FIXTag_OrdType: OrdType_Limit, FIXTag_Price: 100, FIXTag_Side: Side_Buy,
                           FIXTag_HandlInst: HandlInst_AutomatedExecutionOrderPublicBrokerInterventionOk}},
        {'stringFields': {FIXTag_Instrument: 'IBM', FIXTag_Symbol: 'IBM', FIXTag_Text: 'NOFILL'},
         'numericFields': {FIXTag_OrderQty: 500, FIXTag_OrdType: OrdType_Limit, FIXTag_Price: 100, FIXTag_Side: Side_Buy,
                           FIXTag_HandlInst: HandlInst_AutomatedExecutionOrderPublicBrokerInterventionOk}}]))

    # Check we received the same result through the subscription
    for result in order_results.result:
        wait_for_record({
            'stringFields': {'Instrument': result.order.stringFields['Instrument'], 'Text': result.order.stringFields['Text']},
            'numericFields': {'OrdQty': result.order.numericFields['OrdQty'], 'OrdType': result.order.numericFields['OrdType']}})


def send_and_get_orders_one_is_bad(client):
    order_results = client.sendAndGetOrders(SendOrdersRequest(managerName=MANAGER_NAME, message=[
        {'stringFields': {FIXTag_Instrument: 'MSFT', FIXTag_Symbol: 'MSFT', FIXTag_Text: 'NOFILL'},
         'numericFields': {FIXTag_OrderQty: 300, FIXTag_OrdType: OrdType_Limit, FIXTag_Price: 100, FIXTag_Side: Side_Buy,
                           FIXTag_HandlInst: HandlInst_AutomatedExecutionOrderPublicBrokerInterventionOk}},
        {'stringFields': {FIXTag_Instrument: 'IBM', FIXTag_Symbol: 'IBM', FIXTag_Text: 'NOFILL'},
         'numericFields': {FIXTag_OrdType: OrdType_Limit, FIXTag_Price: 100, FIXTag_Side: Side_Buy,
                           FIXTag_HandlInst: HandlInst_AutomatedExecutionOrderPublicBrokerInterventionOk}}]))

    # first order ok, second does not have qty, must produce error in the result
    result = order_results.result[0]
    wait_for_record({
        'stringFields': {'Instrument': result.order.stringFields['Instrument'], 'Text': result.order.stringFields['Text']},
        'numericFields': {'OrdQty': result.order.numericFields['OrdQty'], 'OrdType': result.order.numericFields['OrdType']}})
    assert "error" == order_results.result[1].WhichOneof("result")
    error_check(r'Cannot send a request message with empty or 0 order quantity.*', order_results.result[1].error)


@exception_check('grpc._channel._Rendezvous', r'.*Unknown.*order manager "BadManager".*')
def send_and_get_orders_bad_manager(client):
    order_results = client.sendAndGetOrders(SendOrdersRequest(managerName="BadManager", message=[
        {'stringFields': {FIXTag_Instrument: 'MSFT', FIXTag_Symbol: 'MSFT', FIXTag_Text: 'NOFILL'},
         'numericFields': {FIXTag_OrderQty: 300, FIXTag_OrdType: OrdType_Limit, FIXTag_Price: 100, FIXTag_Side: Side_Buy,
                           FIXTag_HandlInst: HandlInst_AutomatedExecutionOrderPublicBrokerInterventionOk}},
        {'stringFields': {FIXTag_Instrument: 'IBM', FIXTag_Symbol: 'IBM', FIXTag_Text: 'NOFILL'},
         'numericFields': {FIXTag_OrdType: OrdType_Limit, FIXTag_Price: 100, FIXTag_Side: Side_Buy,
                           FIXTag_HandlInst: HandlInst_AutomatedExecutionOrderPublicBrokerInterventionOk}}]))


def modify_orders_message_for_each_order(client):
    order_ids = send_multiple_orders(client)

    client.modifyOrders(
        OrdersRequest(
            orderId=order_ids,
            message=[{'numericFields': {FIXTag_OrderQty: 100}}, {'numericFields': {FIXTag_OrderQty: 200}}]
        )
    )

    wait_for_record(record_id=order_ids[0], expected={
        'stringFields': {'Instrument': 'MSFT', 'Text': 'NOFILL'},
        'numericFields': {'OrdQty': 100, 'OrdType': OrdType_Limit}})
    wait_for_record(record_id=order_ids[1], expected={
        'stringFields': {'Instrument': 'IBM', 'Text': 'NOFILL'},
        'numericFields': {'OrdQty': 200, 'OrdType': OrdType_Limit}})


def modify_orders_one_message_for_all(client):
    order_ids = send_multiple_orders(client)

    client.modifyOrders(
        OrdersRequest(
            orderId=order_ids,
            message=[{'numericFields': {FIXTag_OrdType: OrdType_Market}}]
        )
    )

    wait_for_record(record_id=order_ids[0], expected={
        'stringFields': {'Instrument': 'MSFT', 'Text': 'NOFILL'},
        'numericFields': {'OrdQty': 300, 'OrdType': OrdType_Market}})
    wait_for_record(record_id=order_ids[1], expected={
        'stringFields': {'Instrument': 'IBM', 'Text': 'NOFILL'},
        'numericFields': {'OrdQty': 500, 'OrdType': OrdType_Market}})


@exception_check('grpc._channel._Rendezvous', r'.*Wrong message count. Must be either 1 or a message per each order.*')
def modify_orders_exception_messages_not_matching(client):
    order_id_result = client.sendOrders(
        SendOrdersRequest(
            managerName=MANAGER_NAME,
            message=[
                {'stringFields': {FIXTag_Instrument: 'MSFT', FIXTag_Symbol: 'MSFT', FIXTag_Text: 'NOFILL'},
                 'numericFields': {FIXTag_OrderQty: 300, FIXTag_OrdType: OrdType_Limit, FIXTag_Price: 100, FIXTag_Side: Side_Buy,
                                   FIXTag_HandlInst: HandlInst_AutomatedExecutionOrderPublicBrokerInterventionOk}},
                {'stringFields': {FIXTag_Instrument: 'IBM', FIXTag_Symbol: 'IBM', FIXTag_Text: 'NOFILL'},
                 'numericFields': {FIXTag_OrderQty: 500, FIXTag_OrdType: OrdType_Limit, FIXTag_Price: 100, FIXTag_Side: Side_Buy,
                                   FIXTag_HandlInst: HandlInst_AutomatedExecutionOrderPublicBrokerInterventionOk}},
                {'stringFields': {FIXTag_Instrument: 'IBM', FIXTag_Symbol: 'IBM', FIXTag_Text: 'NOFILL'},
                 'numericFields': {FIXTag_OrderQty: 500, FIXTag_OrdType: OrdType_Limit, FIXTag_Price: 100, FIXTag_Side: Side_Buy,
                                   FIXTag_HandlInst: HandlInst_AutomatedExecutionOrderPublicBrokerInterventionOk}}
            ]
        ))
    order_ids = map(lambda x: x.orderId, order_id_result.result)

    client.modifyOrders(
        OrdersRequest(
            orderId=order_ids,
            message=[{'numericFields': {FIXTag_OrderQty: 100}}, {'numericFields': {FIXTag_OrderQty: 200}}]
        )
    )


def modify_orders_one_is_wrong(client):
    order_ids = send_multiple_orders(client)

    client.modifyOrders(
        OrdersRequest(
            orderId=order_ids,
            message=[{'numericFields': {FIXTag_OrderQty: 100}},
                     {'numericFields': {FIXTag_OrderQty: 0}}]  # Wrong order qty
        )
    )

    wait_for_record(record_id=order_ids[0], expected={
        'stringFields': {'Instrument': 'MSFT', 'Text': 'NOFILL'},
        'numericFields': {'OrdQty': 100, 'OrdType': OrdType_Limit}})
    wait_for_record(record_id=order_ids[1], expected={
        'stringFields': {'Instrument': 'IBM', 'Text': 'NOFILL'},
        'numericFields': {'OrdQty': 500, 'OrdType': OrdType_Limit}})  # Unchanged order


def cancel_orders(client):
    order_ids = send_multiple_orders(client)

    client.cancelOrders(
        OrdersRequest(
            orderId=order_ids
        )
    )

    wait_for_record(record_id=order_ids[0], expected={
        'stringFields': {'Instrument': 'MSFT'},
        'numericFields': {'OrdStatus': ord('4'), 'Leaves': 0}})
    wait_for_record(record_id=order_ids[1], expected={
        'stringFields': {'Instrument': 'IBM'},
        'numericFields': {'OrdStatus': ord('4'), 'Leaves': 0}})

    # Cancel with instruction to broker simulator in Text field to reject cancel request.
    order_ids = send_multiple_orders(client)
    client.cancelOrders(
        OrdersRequest(
            orderId=order_ids,
            message=[{'stringFields': {FIXTag_Text: 'REJECT'}}]
        )
    )

    #OrdState should be '6' - Cxl Rej for both orders
    wait_for_record(record_id=order_ids[0], expected={
        'stringFields': {'Instrument': 'MSFT'},
        'numericFields': {'OrdState': ord('6'), 'Leaves': 300}})
    wait_for_record(record_id=order_ids[1], expected={
        'stringFields': {'Instrument': 'IBM'},
        'numericFields': {'OrdState': ord('6'), 'Leaves': 500}})

    # The same but with a message per order
    order_ids = send_multiple_orders(client)
    client.cancelOrders(
        OrdersRequest(
            orderId=order_ids,
            message=[{'stringFields': {FIXTag_Text: 'REJECT'}},
                     {'stringFields': {FIXTag_Text: 'REJECT'}}]
        )
    )

    #OrdState should be '6' - Cxl Rej for both orders
    wait_for_record(record_id=order_ids[0], expected={
        'stringFields': {'Instrument': 'MSFT'},
        'numericFields': {'OrdState': ord('6'), 'Leaves': 300}})
    wait_for_record(record_id=order_ids[1], expected={
        'stringFields': {'Instrument': 'IBM'},
        'numericFields': {'OrdState': ord('6'), 'Leaves': 500}})


def cancel_all_orders(client):
    order_ids = send_multiple_orders(client)

    client.cancelAllOrders(CancelAllOrdersRequest())

    wait_for_record(record_id=order_ids[0], expected={
        'stringFields': {'Instrument': 'MSFT'},
        'numericFields': {'OrdStatus': ord('4'), 'Leaves': 0}})
    wait_for_record(record_id=order_ids[1], expected={
        'stringFields': {'Instrument': 'IBM'},
        'numericFields': {'OrdStatus': ord('4'), 'Leaves': 0}})

    # Now the same with a filter
    order_ids = send_multiple_orders(client)
    client.cancelAllOrders(CancelAllOrdersRequest(filter = "Instrument = 'MSFT'"))

    wait_for_record(record_id=order_ids[0], expected={
        'stringFields': {'Instrument': 'MSFT'},
        'numericFields': {'OrdStatus': ord('4'), 'Leaves': 0}})
    wait_for_record(record_id=order_ids[1], expected={
        'stringFields': {'Instrument': 'IBM'},
        'numericFields': {'OrdStatus': ord('0'), 'Leaves': 500 }}) # order not canceled because of the filter

    # Cancel all with instruction to broker simulator in Text field to reject cancel request.
    order_ids = send_multiple_orders(client)
    client.cancelAllOrders(CancelAllOrdersRequest(
        message={'stringFields': {FIXTag_Text: 'REJECT'}}
    ))

    #OrdState should be '6' - Cxl Rej for both orders
    wait_for_record(record_id=order_ids[0], expected={
        'stringFields': {'Instrument': 'MSFT'},
        'numericFields': {'OrdState': ord('6'), 'Leaves': 300}})
    wait_for_record(record_id=order_ids[1], expected={
        'stringFields': {'Instrument': 'IBM'},
        'numericFields': {'OrdState': ord('6'), 'Leaves': 500}})


@exception_check('grpc._channel._Rendezvous', r'.*Wrong message count. Must be either 0 or 1 or a message per each order.*')
def cancel_orders_exception_messages_not_matching(client):
    order_ids = send_multiple_orders(client)
    client.cancelOrders(
        OrdersRequest(
            orderId=order_ids,
            message=[{'stringFields': {FIXTag_Text: 'REJECT'}},
                     {'stringFields': {FIXTag_Text: 'REJECT'}},
                     {'stringFields': {FIXTag_Text: 'REJECT'}}]
        )
    )

