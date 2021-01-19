import time

from remote.HFRemoteRequests_pb2 import *
from remote.TMSRemoteEvents_pb2 import *
from utilities.SubscriptionThread import SubscriptionThread
from utilities.Utilities import decimal_equal


class RecordsHolder:
    def __init__(self):
        pass

    time_and_records = []

    @classmethod
    def add_record(cls, record, record_id):
        cls.clean_expired_records()
        cls.time_and_records.append((time.time(), record, record_id))

    @classmethod
    def update_record(cls, record_update, record_id):
        index = len(cls.time_and_records) - 1
        while index >= 0:
            time_and_record = cls.time_and_records[index]
            if record_id == time_and_record[2]:
                cls.apply_update_to_record(record_update, time_and_record[1])
                # inserting a new record because of new time and expiration approach to clean older items in array
                cls.time_and_records.append((time.time(), time_and_record[1], record_id))
                break
            index = index - 1
        cls.clean_expired_records()

    @classmethod
    def apply_update_to_record(cls, record_update, record):
        for field_name in record_update.numericFields:
            record.numericFields[field_name] = record_update.numericFields[field_name]

    @classmethod
    def clean_expired_records(cls):
        expiration_timeout_seconds = 3
        index = len(cls.time_and_records) - 1
        now = time.time()
        while index >= 0:
            record_time = cls.time_and_records[index][0]
            if now - record_time > expiration_timeout_seconds:
                break
            index = index - 1
        if index >= 0:
            del cls.time_and_records[0:index + 1]  # remove all expired records


def order_event_processor(event):
    event_case = event.WhichOneof("event")
    if event_case == 'added':
        RecordsHolder.add_record(event.added.fields, event.added.orderId)
    elif event_case == 'updated':
        RecordsHolder.update_record(event.updated.fields, event.updated.orderId)
    elif event_case == 'feedStatus':
        feed_status = event.feedStatus
        if feed_status == Disconnected:
            pass
        elif feed_status == Reconnected:
            pass
        elif feed_status == InitialStateReceived:
            pass


def target_event_processor(event):
    event_case = event.WhichOneof("event")
    if event_case == 'added':
        RecordsHolder.add_record(event.added.fields, event.added.targetId)
    elif event_case == 'updated':
        RecordsHolder.update_record(event.updated.fields, event.updated.targetId)
    elif event_case == 'feedStatus':
        feed_status = event.feedStatus
        if feed_status == Disconnected:
            pass
        elif feed_status == Reconnected:
            pass
        elif feed_status == InitialStateReceived:
            pass


def target_list_event_processor(event):
    event_case = event.WhichOneof("event")
    if event_case == 'added':
        RecordsHolder.add_record(event.added.fields, event.added.targetListName)
    elif event_case == 'updated':
        RecordsHolder.update_record(event.updated.fields, event.updated.targetListName)
    elif event_case == 'feedStatus':
        feed_status = event.feedStatus
        if feed_status == Disconnected:
            pass
        elif feed_status == Reconnected:
            pass
        elif feed_status == InitialStateReceived:
            pass


order_event_thread = None
target_list_event_thread = None
target_event_thread = None


def subscribe_for_records(client):
    # FIXME all fields arrive, query does not work
    global order_event_thread
    request = SubscribeToOrderRequest(field=['Instrument', 'OrdQty', 'FillQty'])
    order_event_thread = SubscriptionThread(client.subscribeToOutboundOrderData, request, order_event_processor)
    order_event_thread.start()

    # FIXME all fields arrive, query does not work
    global target_list_event_thread
    request = SubscribeToTargetListDataRequest(field=['Name', 'CustomStr1', 'CustomNum1'])
    # TODO same order_event_processor for all record types? rename it
    target_list_event_thread = SubscriptionThread(client.subscribeToTargetListData, request, target_list_event_processor)
    target_list_event_thread.start()

    # FIXME all fields arrive, query does not work
    global target_event_thread
    request = SubscribeToTargetDataRequest(field=['Instrument', 'TgtQty', 'FillQty'])
    # TODO same order_event_processor for all record types? rename it
    target_event_thread = SubscriptionThread(client.subscribeToTargetData, request, target_event_processor)
    target_event_thread.start()


def unsubscribe_from_records():
    order_event_thread.stop()
    target_list_event_thread.stop()
    target_event_thread.stop()


def check_record(expected, record):
    not_matching_field_info = ""
    numeric_fields = expected['numericFields']
    string_fields = expected['stringFields']
    for field in numeric_fields:
        field_not_matching = not decimal_equal(numeric_fields[field], record.numericFields[field])
        if field_not_matching:
            not_matching_field_info = field + ' (expected = ' + str(numeric_fields[field]) + \
                                      ' actual = ' + str(record.numericFields[field]) + ')'
            break
    if not_matching_field_info == "":
        for field in string_fields:
            if string_fields[field] != record.stringFields[field]:
                not_matching_field_info = field + ' (expected = ' + string_fields[field] + \
                                          ' actual = ' + record.stringFields[field] + ')'
                break
    return not_matching_field_info


def wait_for_record(expected, timeout_seconds=5, record_id=-1):
    """
    TODO finish doc
    :param expected:
    :param timeout_seconds:
    :return:
    """
    RecordsHolder.clean_expired_records()
    waiting_time = 0
    while True:
        not_matching_field_info = "no matching record found"
        for time_and_record in reversed(RecordsHolder.time_and_records):
            record = time_and_record[1]
            if record_id != -1:
                stored_record_id = time_and_record[2]
                if stored_record_id == record_id:
                    not_matching_field_info = check_record(expected, record)
                    break
            else:
                not_matching_field_info = check_record(expected, record)
            if not_matching_field_info == "":
                break
        if not_matching_field_info == "":
            break
        else:
            if waiting_time > timeout_seconds:
                string_id = '' if record_id == -1 else str(record_id)
                print('Waiting for record ' + string_id + ' failed. ' + not_matching_field_info)
                print('Expected:', expected)
                raise Exception
            sleep_time = 0.5
            time.sleep(sleep_time)
            waiting_time += sleep_time
