from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

import json

class DHT11(WebsocketConsumer):
    def connect(self):
        self.room_group_name = "room"
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, 
            self.channel_name
        )
        self.accept()
    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, 
            self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                "type": "message",
                "message": text_data,   
            },
        )
    def send(self, text_data=None, bytes_data=None, close=False):
        return super().send(text_data, bytes_data, close)
    
    def message(self, event):
        message = event["message"]
        self.send(
            text_data=json.dumps(
                message
            )
        )
