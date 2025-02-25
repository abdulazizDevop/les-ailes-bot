import aiohttp
import logging
import requests


async def get_eskiz(email, password):
    url = "https://notify.eskiz.uz/api/auth/login"
    payload = {
        'email': email,
        'password': password
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=headers) as response:
            response_data = await response.json()
            logging.info(f"Login dan javob: {response_data}")  # To'liq javobni loglash
            
            if response.status == 200:
                token = response_data.get('data', {}).get('token')
                
                # Token formatini tekshirish
                if token and len(token.split('.')) == 3:
                    return token
                else:
                    logging.error("Noto'g'ri token formati.")
                    return None
            else:
                logging.error(f"Token olishda xatolik: {response_data}")
                return None

    
async def send_sms(phone, token):
    url = "https://notify.eskiz.uz/api/message/sms/send"
    payload = {
        'mobile_phone': phone,
        'message': 'Bu Eskiz dan test',
        'from': '4546',
        'callback_url':'http://callback.url/3/1'
    }
    headers = {
        'Authorization': f"Bearer {token}",
    }
    response = requests.post(url, data=payload, headers=headers)

    if response.status_code != 200:  #UN-OK
        raise Exception(response.text)