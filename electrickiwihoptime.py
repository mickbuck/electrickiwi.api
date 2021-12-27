#Code copied from https://github.com/matthuisman/electrickiwi.api. Changed to get the current setting for the Hour of Power.

import requests
import random
import time

from hashlib import md5

from cryptoJS import encrypt

class ElectricException(Exception):
    pass

class ElectricKiwi(object):
    _secret          = None
    _secret_position = None
    _sid             = None
    _customer        = None

    def __init__(self, at_token=None):
        if at_token:
            self.at_token(at_token)

    def login(self, email, password_hash, customer_index=0):
        payload = {
            'email'   : email,
            'password': password_hash,
        }

        data = self.request('/login/', payload, type='POST')

        self._sid      = data['sid']
        self._customer = data['customer'][customer_index]

        return self._customer

    def password_hash(self, password):
        return md5(password.encode('utf-8')).hexdigest()

    def at_token(self, at_token=None):
        if not at_token:
            data = self.request('/at/')
            at_token = data['token']
            
        self._secret          = at_token[2:-2]
        self._secret_position = int(at_token[:2])

        return at_token

    def request(self, endpoint, params=None, type='GET'):
        params = params or {}

        headers = {
            'x-client': 'ek-app', 
            'x-apiversion': '1_1',
            'user-agent': 'Mozilla/5.0 (Linux; Android 8.1.0; MI 5 Build/OPM7.181205.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/69.0.3497.109 Mobile Safari/537.36',
            'X-Requested-With': 'nz.co.electrickiwi.mobile.app',
        }

        if self._secret:
            headers['x-token'] = self._get_token(endpoint)

        if self._sid:
            headers['x-sid'] = self._sid

        data = requests.request(type, 'https://api.electrickiwi.co.nz{}'.format(endpoint), headers=headers, json=params).json()
        if 'error' in data:
            raise ElectricException(data['error']['detail'])

        return data['data']

    def _get_token(self, endpoint):
        length = random.randint(10, len(self._secret) - 2)
        secret = self._secret[:length]

        data = endpoint + '|' + str(int(time.time())+30) + '|' + ''.join(random.choice('0123456789ABCDEF') for i in range(16))
        encrypted = encrypt(data.encode(), secret.encode()).decode()

        return encrypted[:self._secret_position] + str(length) + encrypted[self._secret_position:]
   
    def _require_login(self):
        if not self._sid:
            raise ElectricException('You need to login first')

    def connection_details(self):
        self._require_login()

        data = self.request('/connection/details/{customer_id}/{connection_id}/'.format(customer_id=self._customer['id'], connection_id=self._customer['connection']['id']))
        return data
    
def hop_time():

    ek       = ElectricKiwi()
    token    = ek.at_token()
    
    loaded = False
    try:
        with open('ek_creds.txt') as f:
            email    = f.readline().strip()
            password = f.readline().strip()

        loaded = True
    except:
        email    = input('EK Email: ')
        password = ek.password_hash(input('EK Password: '))
    
    customer = ek.login(email, password)

    if not loaded and input('Save credentials? Y/N : ').lower() in ('y', 'yes'):
        with open('ek_creds.txt', 'w') as f:
            f.write(email+'\n'+password)

    connection  = ek.connection_details()
    hop = (connection['hop'])
    print(hop['start_time'])
if __name__ == '__main__':
    try:
        hop_time()
    except Exception as e:
            print(e)