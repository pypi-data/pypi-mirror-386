import json
import os
import time
import base64
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Dict, Any
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

try:
    from circle.web3 import configurations
except ImportError:
    configurations = None
try:
    from circle.web3 import developer_controlled_wallets
except ImportError:
    developer_controlled_wallets = None
try:
    from circle.web3 import user_controlled_wallets
except ImportError:
    user_controlled_wallets = None
try:
    from circle.web3 import smart_contract_platform
except ImportError:
    smart_contract_platform = None

CIRCLE_PUBLIC_KEY = None
API_KEY = None
ENTITY_SECRET = None
CONF_CLIENT = None


def init_configurations_client(user_agent=None, **kwargs):
    global CONF_CLIENT
    global API_KEY
    if not CONF_CLIENT:
        if 'api_key' in kwargs:
            API_KEY = kwargs['api_key']
        conf = configurations.Configuration(access_token=API_KEY, **kwargs)
        client = configurations.ApiClient(configuration=conf, user_agent=user_agent)
        CONF_CLIENT = client
        load_public_key()
    return CONF_CLIENT

def init_developer_controlled_wallets_client(api_key=None, entity_secret=None, user_agent=None, **kwargs):
    global API_KEY
    global ENTITY_SECRET
    if api_key is None:
        api_key = load_access_token()
    if entity_secret is None:
        entity_secret = load_entity_secret()
    API_KEY = api_key
    ENTITY_SECRET = entity_secret
    init_configurations_client(user_agent)
    conf = developer_controlled_wallets.Configuration(
        access_token=api_key,
        entity_secret=entity_secret,
        public_key=get_public_key(),
        **kwargs
    )
    return developer_controlled_wallets.ApiClient(configuration=conf, user_agent=user_agent)


def init_user_controlled_wallets_client(api_key=None, user_agent=None, **kwargs):
    global API_KEY
    if api_key is None:
        api_key = load_access_token()
    API_KEY = api_key
    init_configurations_client(user_agent)
    conf = user_controlled_wallets.Configuration(
        access_token=api_key,
        **kwargs
    )
    return user_controlled_wallets.ApiClient(configuration=conf, user_agent=user_agent)


def init_smart_contract_platform_client(api_key=None, entity_secret=None, user_agent=None, **kwargs):
    global API_KEY
    global ENTITY_SECRET
    if api_key is None:
        api_key = load_access_token()
    if entity_secret is None:
        entity_secret = load_entity_secret()
    API_KEY = api_key
    ENTITY_SECRET = entity_secret
    init_configurations_client(user_agent)
    conf = smart_contract_platform.Configuration(
        access_token=api_key,
        entity_secret=entity_secret,
        public_key=get_public_key(),
        **kwargs
    )
    return smart_contract_platform.ApiClient(configuration=conf, user_agent=user_agent)


def load_public_key():
    global CIRCLE_PUBLIC_KEY
    global CONF_CLIENT
    init_configurations_client()
    if not CIRCLE_PUBLIC_KEY:
        api_instance = configurations.DeveloperAccountApi(CONF_CLIENT)
        try:
            api_response = api_instance.get_public_key()
            CIRCLE_PUBLIC_KEY = api_response.data.public_key
        except configurations.ApiException as e:
            print("Exception when calling DeveloperAccountApi->get_public_key: %s\n" % e)


def get_public_key():
    global CIRCLE_PUBLIC_KEY
    if CIRCLE_PUBLIC_KEY is None:
        init_configurations_client()
    return CIRCLE_PUBLIC_KEY


def load_access_token():
    try:
        return os.environ["CIRCLE_WEB3_API_KEY"]
    except KeyError:
        raise Exception("No API Key found")


def load_entity_secret():
    try:
        return os.environ["CIRCLE_ENTITY_SECRET"]
    except KeyError:
        raise Exception("No Entity Secret found")

def generate_entity_secret():
    message = 'Register the following entity secret using the registerEntitySecretCiphertext method or through the Developer Console and save the secret somewhere safe.\n'

    # Generate a random 32-byte secret and convert it to a hex string
    entity_secret = os.urandom(32).hex()
    entity_secret_message = f'!!!! ENTITY SECRET: {entity_secret} !!!!'
    top_bottom_border = '=' * len(entity_secret)

    print(message)
    print(top_bottom_border)
    print(entity_secret_message)
    print(f'{top_bottom_border}\n')
    print(
        'Example Snippet: ' +
        f"""
from circle.web3 import utils

result = utils.register_entity_secret_ciphertext(api_key='<api-key>', entity_secret='{entity_secret}')
print(result)
"""
    )

def resolve_path_relative_to_app_dir(path: str) -> str:
    return os.path.join(os.getcwd(), path)

def register_entity_secret_ciphertext(api_key: str, entity_secret: str, recoveryFileDownloadPath: str = '' , base_url: str = "https://api.circle.com") -> Dict[str, Any]:
    """
    Helper function to register the entity secret for the first time and downloads the recovery file.
    This is a non-idempotent process, so make sure you save the recovery file or the entity secret some place secure.

    :param apiKey: API Key for request authentication.
    :param entity_secret: An Entity secret which you want to register.
    :param recoveryFileDownloadPath: Path to save the recovery file. If not provided, the recovery file will be saved in the current directory.
    :return: Dictionary containing the response data which includes the recovery file.
    """
    global API_KEY
    global ENTITY_SECRET
    if api_key is None:
        api_key = load_access_token()
    if entity_secret is None:
        entity_secret = load_entity_secret()
    API_KEY = api_key
    ENTITY_SECRET = entity_secret

    if recoveryFileDownloadPath != '':
        relative_path = resolve_path_relative_to_app_dir(recoveryFileDownloadPath)
        if not os.path.isdir(relative_path):
            raise ValueError(f'Invalid Directory: {relative_path}')

    entity_secret_ciphertext = generate_entity_secret_ciphertext(api_key, entity_secret)

    url = f"{base_url}/v1/w3s/config/entity/entitySecret"
    base64_regex = r'^([0-9a-zA-Z+/]{4})*(([0-9a-zA-Z+/]{2}==)|([0-9a-zA-Z+/]{3}=))?$'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {api_key}",
        'User-Agent': 'CircleWeb3PythonSDK / DeveloperControlledWallets',
    }

    data = json.dumps({
        'entitySecretCiphertext': entity_secret_ciphertext,
    }).encode('utf-8')

    req = Request(url, data=data, headers=headers, method='POST')

    try:
        with urlopen(req) as response:
            response_data = json.loads(response.read().decode('utf-8'))

        # Write the recovery file content to a file
        if 'recoveryFile' in response_data['data']:
            if re.match(base64_regex, response_data['data']['recoveryFile']):
                message = 'The following entity secret is registered. Remember to save the secret somewhere safe.\n'

                entity_secret_message = f'!!!! ENTITY SECRET: {entity_secret} REGISTERED!!!!'
                top_bottom_border = '=' * len(entity_secret)

                print(message)
                print(top_bottom_border)
                print(entity_secret_message)
                print(f'{top_bottom_border}\n')
                _save_recovery_file(response_data['data']['recoveryFile'], recoveryFileDownloadPath)

        return response_data

    except HTTPError as e:
        if e.code == 409:
            print("Entity secret is already registered")
        print(f"HTTP Error: {e.code} - {e.reason}")
    except URLError as e:
        print(f"URL Error: {e.reason}")
        raise
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

def generate_entity_secret_ciphertext(api_key: str, entity_secret_hex: str) -> str:
    global API_KEY
    global ENTITY_SECRET
    API_KEY = api_key
    ENTITY_SECRET = entity_secret_hex
    entity_secret = bytes.fromhex(entity_secret_hex)
    if len(entity_secret) != 32:
        raise Exception("invalid entity secret")

    # encrypt data by the public key
    public_key = RSA.importKey(get_public_key())
    cipher_rsa = PKCS1_OAEP.new(key=public_key, hashAlgo=SHA256)
    encrypted_data = cipher_rsa.encrypt(entity_secret)

    # encode to base64
    ciphertext = base64.b64encode(encrypted_data)

    return ciphertext.decode()

def _save_recovery_file(recovery_file: str, recovery_path: str) -> None:
    """
    Save the recovery file to the specified path or default location.

    Args:
        recovery_file (str): The recovery file content.
        recovery_path (str): The path to save the recovery file.
    """
    timestamp = int(time.time() * 1000)
    filename = f'recovery_file_{timestamp}.dat'

    try:
        file_path = os.path.join(recovery_path, filename) if recovery_path else filename
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(recovery_file)
        print(f"Recovery file saved successfully at: {file_path}")
    except Exception as error:
        print(f'Error writing recovery file: {error}')
        if recovery_path:
            print('Attempting to write recovery file in the current directory.')
            try:
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(recovery_file)
                print(f"Recovery file saved successfully at: {os.path.abspath(filename)}")
            except Exception as inner_error:
                print(f'Error writing to current directory: {inner_error}')
                print('Recovery file not saved. Please save the below recovery file content manually to a recovery.dat file. \n' + recovery_file)
        else:
            print('Recovery file not saved. Please save the below recovery file content manually to a recovery.dat file. \n' + recovery_file)
