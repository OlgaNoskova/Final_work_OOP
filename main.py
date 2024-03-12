import json
import requests
from datetime import datetime
import time
from tqdm import tqdm
import configparser


def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    token = config.get('VK', 'token')
    user_id = config.get('VK', 'user_id')
    oauth_token = config.get('Yandex', 'OAuth_token')
    config_values = {
        'token': token,
        'user_id': user_id,
        'oauth_token': oauth_token
    }
    return config_values


class VKPHOTOClient:
    API_BASE_URL = 'https://api.vk.com/method'

    def __init__(self, values):
        self.token = values['token']
        self.user_id = values['user_id']

    def get_common_params(self):
        return {
            'access_token': self.token,
            'v': '5.131'
        }

    def users_info(self):
        params = self.get_common_params()
        params.update({'user_ids': self.user_id})
        response = requests.get(f'{self.API_BASE_URL}/users.get', params=params)
        user_data = response.json().get('response')
        id_name = f'{str(user_data[0]['id'])}_{user_data[0]['first_name']}_{user_data[0]['last_name']}'
        return id_name

    def get_profile_photos(self):
        params = self.get_common_params()
        params.update({'owner_id': self.user_id, 'album_id': 'profile', 'extended': 1, 'count': 5})
        response = requests.get(f'{self.API_BASE_URL}/photos.get', params=params)
        return response.json()

    def photo_information(self):
        photos_info = self.get_profile_photos()
        info_list = []
        help_list = []
        album_photo_list = photos_info['response']['items']
        for photo in album_photo_list:
            datetime_ = str(datetime.fromtimestamp(photo['date']))
            date = datetime_.split()
            if photo['likes']['count'] not in help_list:
                info_list.append({'file_name': f'{photo['likes']['count']}.jpg', 'size': photo['sizes'][-1]['type']})
            else:
                info_list.append({'file_name': f'{photo['likes']['count']}_{date[0]}.jpg', 'size': photo['sizes'][-1]['type']})
            help_list.append(photo['likes']['count'])
        return info_list

    def dowanload_url_vk(self):
        photos_info = self.get_profile_photos()
        url_list = []
        album_photo_list = photos_info['response']['items']
        for photo in album_photo_list:
            url_photo_vk = photo['sizes'][-1]['url']
            url_list.append(url_photo_vk)
        return url_list


class YANDEX_DISK:
    API_BASE_URL_YA = 'https://cloud-api.yandex.net'

    def __init__(self, values):
        self.token = values['token']
        self.user_id = values['user_id']
        self.oauth_token = values['oauth_token']
        self.headers = {
            'Authorization': f'OAuth {self.oauth_token}'
        }

    vk_client = VKPHOTOClient(read_config())

    def create_folder(self):
        url_create_dir = f'{self.API_BASE_URL_YA}/v1/disk/resources'
        params = {
            'path': vk_client_.users_info()
        }
        headers = self.headers
        response = requests.put(url_create_dir,
                                params=params,
                                headers=headers)
        return vk_client_.users_info()

    def dowanload_photo(self):
        url_create_dir = f'{self.API_BASE_URL_YA}/v1/disk/resources/upload'
        name_dir = self.create_folder()
        url = vk_client_.dowanload_url_vk()
        photo_name = vk_client_.photo_information()
        for i in range(len(photo_name)):
            params = {
                'path': f'{name_dir}/{photo_name[i]['file_name']}',
                'url': url[i]
            }
            headers = self.headers
            while True:
                response = requests.post(url_create_dir,
                                         params=params,
                                         headers=headers)
                if response.status_code == 202:

                    break
                else:
                    time.sleep(1)
        with open(f'{name_dir}.json', 'w') as file:
            json.dump(photo_name, file, ensure_ascii=False, indent=4)
        progress_bar()


def progress_bar():
    for _ in tqdm(range(len(vk_client_.photo_information()))):
        time.sleep(1)


if __name__ == '__main__':
    vk_client_ = VKPHOTOClient(read_config())
    ya_disk = YANDEX_DISK(read_config())
    ya_disk.dowanload_photo()

