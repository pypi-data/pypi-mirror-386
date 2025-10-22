import requests
import json
from typing import Dict, List, Optional, Callable, Any
import time

class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}/"
        self.command_handlers: Dict[str, Callable] = {}
        self.message_handler: Optional[Callable] = None
        self.callback_handler: Optional[Callable] = None
        self.update_offset = 0
        self.running = False

    def command(self, command_name: str) -> Callable:
        def decorator(func: Callable) -> Callable:
            self.command_handlers[command_name] = func
            return func
        return decorator

    def message(self, func: Callable) -> Callable:
        self.message_handler = func
        return func

    def callback(self, func: Callable) -> Callable:
        self.callback_handler = func
        return func

    def _make_request(self, method: str, data: Optional[Dict] = None, files: Optional[Dict] = None) -> Dict:
        url = self.base_url + method
        if files:
            response = requests.post(url, data=data, files=files, timeout=10)
        else:
            response = requests.post(url, json=data, timeout=10)
        return response.json()

    def reply(self, update: Dict, text: str, parse_mode: Optional[str] = None, reply_markup: Optional[List] = None) -> Dict:
        chat_id = update['message']['chat']['id']
        return self.send(chat_id, text, parse_mode, reply_markup)

    def send(self, chat_id: int, text: str, parse_mode: Optional[str] = None, reply_markup: Optional[List] = None) -> Dict:
        data = {
            'chat_id': chat_id,
            'text': text
        }
        if parse_mode:
            data['parse_mode'] = parse_mode
        if reply_markup:
            if isinstance(reply_markup[0], dict):
                data['reply_markup'] = json.dumps({'inline_keyboard': reply_markup})
            else:
                data['reply_markup'] = json.dumps({'keyboard': reply_markup, 'resize_keyboard': True})
        return self._make_request('sendMessage', data)

    def send_photo(self, chat_id: int, photo_path: str, caption: Optional[str] = None) -> Dict:
        with open(photo_path, 'rb') as photo_file:
            files = {'photo': photo_file}
            data = {'chat_id': chat_id}
            if caption:
                data['caption'] = caption
            return self._make_request('sendPhoto', data, files)

    def reply_photo(self, update: Dict, photo_path: str, caption: Optional[str] = None) -> Dict:
        chat_id = update['message']['chat']['id']
        return self.send_photo(chat_id, photo_path, caption)

    def send_document(self, chat_id: int, document_path: str, caption: Optional[str] = None) -> Dict:
        with open(document_path, 'rb') as doc_file:
            files = {'document': doc_file}
            data = {'chat_id': chat_id}
            if caption:
                data['caption'] = caption
            return self._make_request('sendDocument', data, files)

    def reply_document(self, update: Dict, document_path: str, caption: Optional[str] = None) -> Dict:
        chat_id = update['message']['chat']['id']
        return self.send_document(chat_id, document_path, caption)

    def send_audio(self, chat_id: int, audio_path: str, caption: Optional[str] = None) -> Dict:
        with open(audio_path, 'rb') as audio_file:
            files = {'audio': audio_file}
            data = {'chat_id': chat_id}
            if caption:
                data['caption'] = caption
            return self._make_request('sendAudio', data, files)

    def reply_audio(self, update: Dict, audio_path: str, caption: Optional[str] = None) -> Dict:
        chat_id = update['message']['chat']['id']
        return self.send_audio(chat_id, audio_path, caption)

    def send_video(self, chat_id: int, video_path: str, caption: Optional[str] = None) -> Dict:
        with open(video_path, 'rb') as video_file:
            files = {'video': video_file}
            data = {'chat_id': chat_id}
            if caption:
                data['caption'] = caption
            return self._make_request('sendVideo', data, files)

    def reply_video(self, update: Dict, video_path: str, caption: Optional[str] = None) -> Dict:
        chat_id = update['message']['chat']['id']
        return self.send_video(chat_id, video_path, caption)

    def send_poll(self, chat_id: int, question: str, options: List[str]) -> Dict:
        data = {
            'chat_id': chat_id,
            'question': question,
            'options': json.dumps(options)
        }
        return self._make_request('sendPoll', data)

    def reply_poll(self, update: Dict, question: str, options: List[str]) -> Dict:
        chat_id = update['message']['chat']['id']
        return self.send_poll(chat_id, question, options)

    def send_dice(self, chat_id: int) -> Dict:
        data = {'chat_id': chat_id}
        return self._make_request('sendDice', data)

    def reply_dice(self, update: Dict) -> Dict:
        chat_id = update['message']['chat']['id']
        return self.send_dice(chat_id)

    def send_location(self, chat_id: int, latitude: float, longitude: float) -> Dict:
        data = {
            'chat_id': chat_id,
            'latitude': latitude,
            'longitude': longitude
        }
        return self._make_request('sendLocation', data)

    def reply_location(self, update: Dict, latitude: float, longitude: float) -> Dict:
        chat_id = update['message']['chat']['id']
        return self.send_location(chat_id, latitude, longitude)

    def send_contact(self, chat_id: int, phone_number: str, first_name: str) -> Dict:
        data = {
            'chat_id': chat_id,
            'phone_number': phone_number,
            'first_name': first_name
        }
        return self._make_request('sendContact', data)

    def reply_contact(self, update: Dict, phone_number: str, first_name: str) -> Dict:
        chat_id = update['message']['chat']['id']
        return self.send_contact(chat_id, phone_number, first_name)

    def edit_message(self, chat_id: int, message_id: int, new_text: str, parse_mode: Optional[str] = None, inline_keyboard: Optional[List] = None) -> Dict:
        data = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': new_text
        }
        if parse_mode:
            data['parse_mode'] = parse_mode
        if inline_keyboard:
            data['reply_markup'] = json.dumps({'inline_keyboard': inline_keyboard})
        return self._make_request('editMessageText', data)

    def delete_message(self, chat_id: int, message_id: int) -> Dict:
        data = {
            'chat_id': chat_id,
            'message_id': message_id
        }
        return self._make_request('deleteMessage', data)

    def pin_message(self, chat_id: int, message_id: int) -> Dict:
        data = {
            'chat_id': chat_id,
            'message_id': message_id
        }
        return self._make_request('pinChatMessage', data)

    def unpin_message(self, chat_id: int, message_id: int) -> Dict:
        data = {
            'chat_id': chat_id,
            'message_id': message_id
        }
        return self._make_request('unpinChatMessage', data)

    def answer_callback(self, update: Dict, text: Optional[str] = None, show_alert: bool = False) -> Dict:
        callback_query_id = update['callback_query']['id']
        data = {
            'callback_query_id': callback_query_id,
            'show_alert': show_alert
        }
        if text:
            data['text'] = text
        return self._make_request('answerCallbackQuery', data)

    def get_me(self) -> Dict:
        return self._make_request('getMe')

    def _process_update(self, update: Dict):
        if 'message' in update:
            message = update['message']
            if 'text' in message:
                text = message['text']
                if text.startswith('/'):
                    parts = text.split()
                    command = parts[0][1:]
                    if command in self.command_handlers:
                        self.command_handlers[command](update, self)
                    return
                
                if self.message_handler:
                    self.message_handler(update, self)
            
        elif 'callback_query' in update:
            if self.callback_handler:
                self.callback_handler(update, self)

    def start(self):
        self.running = True
        while self.running:
            try:
                data = {'offset': self.update_offset, 'timeout': 30}
                response = self._make_request('getUpdates', data)
                
                if response.get('ok'):
                    updates = response['result']
                    for update in updates:
                        self.update_offset = update['update_id'] + 1
                        self._process_update(update)
                time.sleep(1)
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)

    def stop(self):
        self.running = False

def starexx():
    return print("Ankit Mehta (realstarexx)")
def telegram(token: str) -> TelegramBot:
    return TelegramBot(token)