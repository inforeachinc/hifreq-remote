from EventThread import EventThread

from utilities.IterableQueue import IterableQueue


class SubscriptionThread(EventThread):
    def __init__(self, subscription_function, subscription_request, processor):
        self.queue = IterableQueue(subscription_request)
        EventThread.__init__(self, subscription_function(iter(self.queue)), processor)

    def stop(self):
        self.queue.close()
        self.join()
