from pypers.core.interfaces.msgbus.base import MSGBase
from pypers.core.interfaces.msgbus.test import MockSQS
from pypers.core.interfaces import db
import os
import boto3
import json


class SQS(MSGBase):

    processing_messages = {}

    def __init__(self):
        if os.environ.get("SQS_URL", None):
            endpoint_url = os.environ['SQS_URL']
        else:
            endpoint_url = None
        if os.environ.get("GITHUB_TOKEN", None):
            self.msgbus = MockSQS()
        else:
            self.msgbus = boto3.resource('sqs',
                                         endpoint_url=endpoint_url)

        self.queue_name = os.environ.get("GBD_QUEUE", 'gbd_pypers')
        super(SQS, self).__init__()

    def get_pypers_queue(self):
        try:
            queue = self.msgbus.get_queue_by_name(QueueName=self.queue_name)
        except Exception as e:
            queue = self.msgbus.create_queue(
                QueueName=self.queue_name,
                Attributes={'DelaySeconds': '0'})
        self.queue = queue

    def reset_history(self, runid, collection):
        db.get_seen_steps().reset_history(runid, collection)

    def send_message(self, runid,
                     collection=None, step=None, index=None,
                     custom_config=None, restart=False, restart_step=False, type=None, retry=False,
                     selected_queue=None):
        if restart_step:
            db.get_seen_steps().reset_step(runid, collection, step)
        if step and db.get_seen_steps().step_visited(
                runid, collection, step, sub_step=index):
            return
        body = {
            'runid': runid,
            'collection': collection,
            'type': type,
            'step': step,
            'index': index,
            'custom_config': custom_config,
            'force_restart': restart,
            'retry': retry
        }
        while True:
            queue_to_send = self.queue_name
            if selected_queue:
                queue_to_send = selected_queue
            resp = self.queue.send_message(
                MessageBody=json.dumps(body),
                MessageAttributes={
                    'type': {
                        'StringValue': queue_to_send,
                        'DataType': 'String'
                    }
                })
            if not resp.get('Failed', None):
                break

    def get_messges(self):
        messages = self.queue.receive_messages(
            AttributeNames=[
                'All',
            ],
            MessageAttributeNames=[
                'type',
            ],
            MaxNumberOfMessages=1,
            VisibilityTimeout=60*60*5,
            WaitTimeSeconds=5,
        )
        if len(messages) > 0:
            message = messages[0]
        else:
            message = None
        if message:
            self.processing_messages[message.message_id] = message
            body = json.loads(message.body)
            return (body, message.message_id)
        return None, None

    def delete_message(self, message_id):
        message = self.processing_messages.pop(message_id, None)
        if message:
            message.delete()
