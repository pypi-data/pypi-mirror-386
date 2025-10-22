import re
import os
import io
import time
from pathlib import Path
import sys
import platform
import logging
from math import sqrt, floor
import json
import base64
from urllib.parse import urlparse, parse_qs

import numpy as np
import rapidfuzz.fuzz
from PIL import Image
from loguru import logger
import regex
import requests


try:
    from GameSentenceMiner.util.electron_config import get_ocr_language, get_furigana_filter_sensitivity
    from GameSentenceMiner.util.configuration import CommonLanguages
except ImportError:
    pass

# from GameSentenceMiner.util.configuration import get_temporary_directory

try:
    from manga_ocr import MangaOcr as MOCR
except ImportError:
    pass

try:
    import Vision
    import objc
    from AppKit import NSData, NSImage, NSBundle
    from CoreFoundation import CFRunLoopRunInMode, kCFRunLoopDefaultMode, CFRunLoopStop, CFRunLoopGetCurrent
except ImportError:
    pass

try:
    from google.cloud import vision
    from google.oauth2 import service_account
    from google.api_core.exceptions import ServiceUnavailable
except ImportError:
    pass

try:
    from azure.ai.vision.imageanalysis import ImageAnalysisClient
    from azure.ai.vision.imageanalysis.models import VisualFeatures
    from azure.core.credentials import AzureKeyCredential
    from azure.core.exceptions import ServiceRequestError
except ImportError:
    pass

try:
    import easyocr
except ImportError:
    pass

try:
    from rapidocr_onnxruntime import RapidOCR as ROCR
    import urllib.request
except ImportError:
    pass

try:
    import winocr
except ImportError:
    pass

try:
    try:
        if os.path.exists(os.path.expanduser('~/.config/oneocr/oneocr.dll')):
            import oneocr
    except Exception as e:
        oneocr = None
        logger.warning(f'Failed to import OneOCR: {e}', exc_info=True)
except ImportError:
    pass

try:
    import pyjson5
except ImportError:
    pass

try:
    import betterproto
    from GameSentenceMiner.owocr.owocr.lens_betterproto import *
    import random
except ImportError:
    pass

try:
    import fpng_py
    optimized_png_encode = True
except:
    optimized_png_encode = False


def empty_post_process(text):
    return text


def post_process(text, keep_blank_lines=False):
    import jaconv
    text = text.replace("\"", "")
    if keep_blank_lines:
        text = '\n'.join([''.join(i.split()) for i in text.splitlines()])
    else:
        text = ''.join([''.join(i.split()) for i in text.splitlines()])
    text = text.replace('…', '・・・')
    text = re.sub('[・.]{2,}', lambda x: (x.end() - x.start()) * '・', text)
    text = re.sub(r'・{3,}', '・・・', text)
    text = jaconv.h2z(text, ascii=True, digit=True)
    return text


def input_to_pil_image(img):
    is_path = False
    if isinstance(img, Image.Image):
        pil_image = img
    elif isinstance(img, (bytes, bytearray)):
        pil_image = Image.open(io.BytesIO(img))
    elif isinstance(img, Path):
        is_path = True
        try:
            pil_image = Image.open(img)
            pil_image.load()
        except (UnidentifiedImageError, OSError) as e:
            return None
    else:
        raise ValueError(f'img must be a path, PIL.Image or bytes object, instead got: {img}')
    return pil_image, is_path


def pil_image_to_bytes(img, img_format='png', png_compression=6, jpeg_quality=80, optimize=False):
    if img_format == 'png' and optimized_png_encode and not optimize:
        raw_data = img.convert('RGBA').tobytes()
        image_bytes = fpng_py.fpng_encode_image_to_memory(raw_data, img.width, img.height)
    else:
        image_bytes = io.BytesIO()
        if img_format == 'jpeg':
            img = img.convert('RGB')
        img.save(image_bytes, format=img_format, compress_level=png_compression, quality=jpeg_quality, optimize=optimize, subsampling=0)
        image_bytes = image_bytes.getvalue()
    return image_bytes


def pil_image_to_numpy_array(img):
    return np.array(img.convert('RGBA'))


def limit_image_size(img, max_size):
    img_bytes = pil_image_to_bytes(img)
    if len(img_bytes) <= max_size:
        return img_bytes, 'png'

    scaling_factor = 0.60 if any(x > 2000 for x in img.size) else 0.75
    new_w = int(img.width * scaling_factor)
    new_h = int(img.height * scaling_factor)
    resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    resized_img_bytes = pil_image_to_bytes(resized_img)
    if len(resized_img_bytes) <= max_size:
        return resized_img_bytes, 'png'

    for _ in range(2):
        jpeg_quality = 80
        while jpeg_quality >= 60:
            img_bytes = pil_image_to_bytes(img, 'jpeg', jpeg_quality=jpeg_quality, optimize=True)
            if len(img_bytes) <= max_size:
                return img_bytes, 'jpeg'
            jpeg_quality -= 5
        img = resized_img

    return False, ''


def get_regex(lang):
    if lang == "ja":
        return re.compile(r'[\u3041-\u3096\u30A1-\u30FA\u4E00-\u9FFF]')
    elif lang == "zh":
        return re.compile(r'[\u4E00-\u9FFF]')
    elif lang == "ko":
        return re.compile(r'[\uAC00-\uD7AF]')
    elif lang == "ar":
        return re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
    elif lang == "ru":
        return re.compile(r'[\u0400-\u04FF\u0500-\u052F\u2DE0-\u2DFF\uA640-\uA69F\u1C80-\u1C8F]')
    elif lang == "el":
        return re.compile(r'[\u0370-\u03FF\u1F00-\u1FFF]')
    elif lang == "he":
        return re.compile(r'[\u0590-\u05FF\uFB1D-\uFB4F]')
    elif lang == "th":
        return re.compile(r'[\u0E00-\u0E7F]')
    else:
        return re.compile(
        r'[a-zA-Z\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u0250-\u02AF\u1D00-\u1D7F\u1D80-\u1DBF\u1E00-\u1EFF\u2C60-\u2C7F\uA720-\uA7FF\uAB30-\uAB6F]')


class MangaOcr:
    name = 'mangaocr'
    readable_name = 'Manga OCR'
    key = 'm'
    available = False

    def __init__(self, config={'pretrained_model_name_or_path':'kha-white/manga-ocr-base','force_cpu': False}, lang='ja'):
        if 'manga_ocr' not in sys.modules:
            logger.warning('manga-ocr not available, Manga OCR will not work!')
        else:
            logger.disable('manga_ocr')
            logging.getLogger('transformers').setLevel(logging.ERROR) # silence transformers >=4.46 warnings
            from manga_ocr import ocr
            ocr.post_process = empty_post_process
            logger.info(f'Loading Manga OCR model')
            self.model = MOCR(config['pretrained_model_name_or_path'], config['force_cpu'])
            self.available = True
            logger.info('Manga OCR ready')

    def __call__(self, img, furigana_filter_sensitivity=0):
        img, is_path = input_to_pil_image(img)
        if not img:
            return (False, 'Invalid image provided')

        x = (True, self.model(img))

        # img.close()
        return x

class GoogleVision:
    name = 'gvision'
    readable_name = 'Google Vision'
    key = 'g'
    available = False

    def __init__(self, lang='ja'):
        if 'google.cloud' not in sys.modules:
            logger.warning('google-cloud-vision not available, Google Vision will not work!')
        else:
            logger.info(f'Parsing Google credentials')
            google_credentials_file = os.path.join(os.path.expanduser('~'),'.config','google_vision.json')
            try:
                google_credentials = service_account.Credentials.from_service_account_file(google_credentials_file)
                self.client = vision.ImageAnnotatorClient(credentials=google_credentials)
                self.available = True
                logger.info('Google Vision ready')
            except:
                logger.warning('Error parsing Google credentials, Google Vision will not work!')

    def __call__(self, img, furigana_filter_sensitivity=0):
        img, is_path = input_to_pil_image(img)
        if not img:
            return (False, 'Invalid image provided')

        image_bytes = self._preprocess(img)
        image = vision.Image(content=image_bytes)
        try:
            response = self.client.text_detection(image=image)
        except ServiceUnavailable:
            return (False, 'Connection error!')
        except:
            return (False, 'Unknown error!')
        texts = response.text_annotations
        res = texts[0].description if len(texts) > 0 else ''
        x = (True, res)

        # img.close()
        return x

    def _preprocess(self, img):
        return pil_image_to_bytes(img)

class GoogleLens:
    name = 'glens'
    readable_name = 'Google Lens'
    key = 'l'
    available = False

    def __init__(self, lang='ja', get_furigana_sens_from_file=True):
        import regex
        self.regex = get_regex(lang)
        self.initial_lang = lang
        self.punctuation_regex = regex.compile(r'[\p{P}\p{S}]')
        self.get_furigana_sens_from_file = get_furigana_sens_from_file
        if 'betterproto' not in sys.modules:
            logger.warning('betterproto not available, Google Lens will not work!')
        else:
            self.available = True
            logger.info('Google Lens ready')

    def __call__(self, img, furigana_filter_sensitivity=0, return_coords=False):
        if self.get_furigana_sens_from_file:
            furigana_filter_sensitivity = get_furigana_filter_sensitivity()
        else:
            furigana_filter_sensitivity = furigana_filter_sensitivity
        lang = get_ocr_language()
        img, is_path = input_to_pil_image(img)
        if lang != self.initial_lang:
            self.initial_lang = lang
            self.regex = get_regex(lang)
        if not img:
            return (False, 'Invalid image provided')

        request = LensOverlayServerRequest()

        request.objects_request.request_context.request_id.uuid = random.randint(0, 2**64 - 1)
        request.objects_request.request_context.request_id.sequence_id = 0
        request.objects_request.request_context.request_id.image_sequence_id = 0
        request.objects_request.request_context.request_id.analytics_id = random.randbytes(16)
        request.objects_request.request_context.request_id.routing_info = LensOverlayRoutingInfo()

        request.objects_request.request_context.client_context.platform = Platform.WEB
        request.objects_request.request_context.client_context.surface = Surface.CHROMIUM

        request.objects_request.request_context.client_context.locale_context.language = 'ja'
        request.objects_request.request_context.client_context.locale_context.region = 'Asia/Tokyo'
        request.objects_request.request_context.client_context.locale_context.time_zone = '' # not set by chromium

        request.objects_request.request_context.client_context.app_id = '' # not set by chromium

        filter = AppliedFilter()
        filter.filter_type = LensOverlayFilterType.AUTO_FILTER
        request.objects_request.request_context.client_context.client_filters.filter.append(filter)

        image_data = self._preprocess(img)
        request.objects_request.image_data.payload.image_bytes = image_data[0]
        request.objects_request.image_data.image_metadata.width = image_data[1]
        request.objects_request.image_data.image_metadata.height = image_data[2]

        payload = request.SerializeToString()

        headers = {
            'Host': 'lensfrontend-pa.googleapis.com',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-protobuf',
            'X-Goog-Api-Key': 'AIzaSyDr2UxVnv_U85AbhhY8XSHSIavUW0DC-sY',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Dest': 'empty',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'ja-JP;q=0.6,ja;q=0.5'
        }

        try:
            res = requests.post('https://lensfrontend-pa.googleapis.com/v1/crupload', data=payload, headers=headers, timeout=5)
        except requests.exceptions.Timeout:
            return (False, 'Request timeout!')
        except requests.exceptions.ConnectionError:
            return (False, 'Connection error!')

        if res.status_code != 200:
            return (False, 'Unknown error!')

        response_proto = LensOverlayServerResponse().FromString(res.content)
        response_dict = response_proto.to_dict(betterproto.Casing.SNAKE)

        if os.path.exists(r"C:\Users\Beangate\GSM\test"):
            with open(os.path.join(r"C:\Users\Beangate\GSM\test", 'glens_response.json'), 'w', encoding='utf-8') as f:
                json.dump(response_dict, f, indent=4, ensure_ascii=False)
        res = ''
        text = response_dict['objects_response']['text']
        skipped = []
        previous_line = None
        filtered_response_dict = response_dict
        if furigana_filter_sensitivity:
            import copy
            filtered_response_dict = copy.deepcopy(response_dict)
            filtered_paragraphs = []
        
        if 'text_layout' in text:
            for paragraph in text['text_layout']['paragraphs']:
                if previous_line:
                    prev_bbox = previous_line['geometry']['bounding_box']
                    curr_bbox = paragraph['geometry']['bounding_box']
                    vertical_space = abs(curr_bbox['center_y'] - prev_bbox['center_y']) * img.height
                    prev_height = prev_bbox['height'] * img.height
                    current_height = curr_bbox['height'] * img.height
                    avg_height = (prev_height + current_height) / 2
                    # If vertical space is close to previous line's height, add a blank line
                    # logger.info(f"Vertical space: {vertical_space}, Average height: {avg_height}")
                    # logger.info(avg_height * 2)
                    if vertical_space > avg_height * 2:
                        res += 'BLANK_LINE\n'
                passed_furigana_filter_lines = []
                for line in paragraph['lines']:
                    if furigana_filter_sensitivity:
                        line_width = line['geometry']['bounding_box']['width'] * img.width
                        line_height = line['geometry']['bounding_box']['height'] * img.height
                        passes = False
                        for word in line['words']:
                            if self.punctuation_regex.findall(word['plain_text']):
                                res += word['plain_text'] + word['text_separator']
                                continue
                            if line_width > furigana_filter_sensitivity and line_height > furigana_filter_sensitivity:
                                res += word['plain_text'] + word['text_separator']
                                passes = True
                            else:
                                skipped.extend(word['plain_text'])
                                continue
                        if passes:
                            passed_furigana_filter_lines.append(line)
                    else:
                        for word in line['words']:
                            res += word['plain_text'] + word['text_separator']
                    res += '\n'

                if furigana_filter_sensitivity and passed_furigana_filter_lines:
                    # Create a filtered paragraph with only the passing lines
                    filtered_paragraph = paragraph.copy()
                    filtered_paragraph['lines'] = passed_furigana_filter_lines
                    filtered_paragraphs.append(filtered_paragraph)
                
                previous_line = paragraph
            
            if furigana_filter_sensitivity:
                filtered_response_dict['objects_response']['text']['text_layout']['paragraphs'] = filtered_paragraphs
            
            res += '\n'
            # logger.info(
            #     f"Skipped {len(skipped)} chars due to furigana filter sensitivity: {furigana_filter_sensitivity}")
            # widths = []
            # heights = []
            # if 'text_layout' in text:
            #     paragraphs = text['text_layout']['paragraphs']
            #     for paragraph in paragraphs:
            #         for line in paragraph['lines']:
            #             for word in line['words']:
            #                 if self.kana_kanji_regex.search(word['plain_text']) is None:
            #                     continue
            #                 widths.append(word['geometry']['bounding_box']['width'])
            #                 heights.append(word['geometry']['bounding_box']['height'])
            #
            # max_width = max(sorted(widths)[:-max(1, len(widths) // 10)]) if len(widths) > 1 else 0
            # max_height = max(sorted(heights)[:-max(1, len(heights) // 10)]) if len(heights) > 1 else 0
            #
            # required_width = max_width * furigana_filter_sensitivity
            # required_height = max_height * furigana_filter_sensitivity
            #
            # if 'text_layout' in text:
            #     paragraphs = text['text_layout']['paragraphs']
            #     for paragraph in paragraphs:
            #         for line in paragraph['lines']:
            #             if furigana_filter_sensitivity == 0 or line['geometry']['bounding_box']['width'] > required_width or line['geometry']['bounding_box']['height'] > required_height:
            #                 for word in line['words']:
            #                         res += word['plain_text'] + word['text_separator']
            #             else:
            #                 continue
            #         res += '\n'
        # else:
        #     if 'text_layout' in text:
        #         paragraphs = text['text_layout']['paragraphs']
        #         for paragraph in paragraphs:
        #             for line in paragraph['lines']:
        #                 for word in line['words']:
        #                         res += word['plain_text'] + word['text_separator']
        #                 else:
        #                     continue
        #             res += '\n'
        
        if return_coords:
            x = (True, res, filtered_response_dict)
        else:
            x = (True, res)

        if skipped:
            logger.info(f"Skipped {len(skipped)} chars due to furigana filter sensitivity: {furigana_filter_sensitivity}")
            logger.debug(f"Skipped chars: {''.join(skipped)}")

        # img.close()
        return x

    def _preprocess(self, img):
        if img.width * img.height > 3000000:
            aspect_ratio = img.width / img.height
            new_w = int(sqrt(3000000 * aspect_ratio))
            new_h = int(new_w / aspect_ratio)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        return (pil_image_to_bytes(img), img.width, img.height)

class GoogleLensWeb:
    name = 'glensweb'
    readable_name = 'Google Lens (web)'
    key = 'k'
    available = False

    def __init__(self, lang='ja'):
        if 'pyjson5' not in sys.modules:
            logger.warning('pyjson5 not available, Google Lens (web) will not work!')
        else:
            self.requests_session = requests.Session()
            self.available = True
            logger.info('Google Lens (web) ready')

    def __call__(self, img, furigana_filter_sensitivity=0):
        img, is_path = input_to_pil_image(img)
        if not img:
            return (False, 'Invalid image provided')

        url = 'https://lens.google.com/v3/upload'
        files = {'encoded_image': ('image.png', self._preprocess(img), 'image/png')}
        headers = {
            'Host': 'lens.google.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja-JP;q=0.6,ja;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Referer': 'https://www.google.com/',
            'Origin': 'https://www.google.com',
            'Alt-Used': 'lens.google.com',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-site',
            'Priority': 'u=0, i',
            'TE': 'trailers'
        }
        cookies = {'SOCS': 'CAESEwgDEgk0ODE3Nzk3MjQaAmVuIAEaBgiA_LyaBg'}

        try:
            res = self.requests_session.post(url, files=files, headers=headers, cookies=cookies, timeout=5, allow_redirects=False)
        except requests.exceptions.Timeout:
            return (False, 'Request timeout!')
        except requests.exceptions.ConnectionError:
            return (False, 'Connection error!')

        if res.status_code != 303:
            return (False, 'Unknown error!')

        redirect_url = res.headers.get('Location')
        if not redirect_url:
            return (False, 'Error getting redirect URL!')

        parsed_url = urlparse(redirect_url)
        query_params = parse_qs(parsed_url.query)

        if ('vsrid' not in query_params) or ('gsessionid' not in query_params):
            return (False, 'Unknown error!')

        try:
            res = self.requests_session.get(f"https://lens.google.com/qfmetadata?vsrid={query_params['vsrid'][0]}&gsessionid={query_params['gsessionid'][0]}", timeout=5)
        except requests.exceptions.Timeout:
            return (False, 'Request timeout!')
        except requests.exceptions.ConnectionError:
            return (False, 'Connection error!')

        if (len(res.text.splitlines()) != 3):
            return (False, 'Unknown error!')

        lens_object = pyjson5.loads(res.text.splitlines()[2])

        res = ''
        text = lens_object[0][2][0][0]
        for paragraph in text:
            for line in paragraph[1]:
                for word in line[0]:
                    res += word[1] + word[2]
            res += '\n'

        x = (True, res)

        # img.close()
        return x

    def _preprocess(self, img):
        if img.width * img.height > 3000000:
            aspect_ratio = img.width / img.height
            new_w = int(sqrt(3000000 * aspect_ratio))
            new_h = int(new_w / aspect_ratio)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        return pil_image_to_bytes(img)

class Bing:
    name = 'bing'
    readable_name = 'Bing'
    key = 'b'
    available = False

    def __init__(self, lang='ja'):
        self.requests_session = requests.Session()
        self.available = True
        logger.info('Bing ready')

    def __call__(self, img, furigana_filter_sensitivity=0):
        img, is_path = input_to_pil_image(img)
        if not img:
            return (False, 'Invalid image provided')

        img_bytes = self._preprocess(img)
        if not img_bytes:
            return (False, 'Image is too big!')

        upload_url = 'https://www.bing.com/images/search?view=detailv2&iss=sbiupload'
        upload_headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'ja-JP;q=0.6,ja;q=0.5',
            'cache-control': 'max-age=0',
            'origin': 'https://www.bing.com',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0',
        }
        files = {
            'imgurl': (None, ''),
            'cbir': (None, 'sbi'),
            'imageBin': (None, img_bytes)
        }

        for _ in range(2):
            api_host = urlparse(upload_url).netloc
            try:
                res = self.requests_session.post(upload_url, headers=upload_headers, files=files, timeout=5, allow_redirects=False)
            except requests.exceptions.Timeout:
                return (False, 'Request timeout!')
            except requests.exceptions.ConnectionError:
                return (False, 'Connection error!')

            if res.status_code != 302:
                return (False, 'Unknown error!')

            redirect_url = res.headers.get('Location')
            if not redirect_url:
                return (False, 'Error getting redirect URL!')
            if not redirect_url.startswith('https://'):
                break
            upload_url = redirect_url

        parsed_url = urlparse(redirect_url)
        query_params = parse_qs(parsed_url.query)

        image_insights_token = query_params.get('insightsToken')
        if not image_insights_token:
            return (False, 'Error getting token!')
        image_insights_token = image_insights_token[0]

        api_url = f'https://{api_host}/images/api/custom/knowledge'
        api_headers = {
            'accept': '*/*',
            'accept-language': 'ja-JP;q=0.6,ja;q=0.5',
            'origin': 'https://www.bing.com',
            'referer': f'https://www.bing.com/images/search?view=detailV2&insightstoken={image_insights_token}',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0',
        }
        api_data_json = {
            'imageInfo': {'imageInsightsToken': image_insights_token, 'source': 'Url'},
            'knowledgeRequest': {'invokedSkills': ['OCR'], 'index': 1}
        }
        files = {
            'knowledgeRequest': (None, json.dumps(api_data_json), 'application/json')
        }

        try:
            res = self.requests_session.post(api_url, headers=api_headers, files=files, timeout=5)
        except requests.exceptions.Timeout:
            return (False, 'Request timeout!')
        except requests.exceptions.ConnectionError:
            return (False, 'Connection error!')

        if res.status_code != 200:
            return (False, 'Unknown error!')

        data = res.json()

        res = ''
        text_tag = None
        for tag in data['tags']:
            if tag.get('displayName') == '##TextRecognition':
                text_tag = tag
                break
        if text_tag:
            text_action = None
            for action in text_tag['actions']:
                if action.get('_type') == 'ImageKnowledge/TextRecognitionAction':
                    text_action = action
                    break
            if text_action:
                regions = text_action['data'].get('regions', [])
                for region in regions:
                    for line in region.get('lines', []):
                        res += line['text'] + '\n'

        x = (True, res)

        # img.close()
        return x

    def _preprocess(self, img):
        max_pixel_size = 4000
        max_byte_size = 767772
        res = None

        if any(x > max_pixel_size for x in img.size):
            resize_factor = max(max_pixel_size / img.width, max_pixel_size / img.height)
            new_w = int(img.width * resize_factor)
            new_h = int(img.height * resize_factor)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        img_bytes, _ = limit_image_size(img, max_byte_size)

        if img_bytes:
            res = base64.b64encode(img_bytes).decode('utf-8')

        return res

class AppleVision:
    name = 'avision'
    readable_name = 'Apple Vision'
    key = 'a'
    available = False

    def __init__(self, lang='ja'):
        if sys.platform != 'darwin':
            logger.warning('Apple Vision is not supported on non-macOS platforms!')
        elif int(platform.mac_ver()[0].split('.')[0]) < 13:
            logger.warning('Apple Vision is not supported on macOS older than Ventura/13.0!')
        else:
            self.available = True
            logger.info('Apple Vision ready')

    def __call__(self, img, furigana_filter_sensitivity=0):
        img, is_path = input_to_pil_image(img)
        if not img:
            return (False, 'Invalid image provided')

        with objc.autorelease_pool():
            req = Vision.VNRecognizeTextRequest.alloc().init()

            req.setRevision_(Vision.VNRecognizeTextRequestRevision3)
            req.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
            req.setUsesLanguageCorrection_(True)
            req.setRecognitionLanguages_(['ja','en'])

            handler = Vision.VNImageRequestHandler.alloc().initWithData_options_(
                self._preprocess(img), None
            )

            success = handler.performRequests_error_([req], None)
            res = ''
            if success[0]:
                for result in req.results():
                    res += result.text() + '\n'
                x = (True, res)
            else:
                x = (False, 'Unknown error!')

            # img.close()
            return x

    def _preprocess(self, img):
        return pil_image_to_bytes(img, 'tiff')


class AppleLiveText:
    name = 'alivetext'
    readable_name = 'Apple Live Text'
    key = 'd'
    available = False

    def __init__(self, lang='ja'):
        if sys.platform != 'darwin':
            logger.warning('Apple Live Text is not supported on non-macOS platforms!')
        elif int(platform.mac_ver()[0].split('.')[0]) < 13:
            logger.warning('Apple Live Text is not supported on macOS older than Ventura/13.0!')
        else:
            app_info = NSBundle.mainBundle().infoDictionary()
            app_info['LSBackgroundOnly'] = '1'
            self.VKCImageAnalyzer = objc.lookUpClass('VKCImageAnalyzer')
            self.VKCImageAnalyzerRequest = objc.lookUpClass('VKCImageAnalyzerRequest')
            objc.registerMetaDataForSelector(
                b'VKCImageAnalyzer',
                b'processRequest:progressHandler:completionHandler:',
                {
                    'arguments': {
                        3: {
                            'callable': {
                                'retval': {'type': b'v'},
                                'arguments': {
                                    0: {'type': b'^v'},
                                    1: {'type': b'd'},
                                }
                            }
                        },
                        4: {
                            'callable': {
                                'retval': {'type': b'v'},
                                'arguments': {
                                    0: {'type': b'^v'},
                                    1: {'type': b'@'},
                                    2: {'type': b'@'},
                                }
                            }
                        }
                    }
                }
            )
            self.available = True
            logger.info('Apple Live Text ready')

    def __call__(self, img, furigana_filter_sensitivity=0):
        img, is_path = input_to_pil_image(img)
        if not img:
            return (False, 'Invalid image provided')

        with objc.autorelease_pool():
            analyzer = self.VKCImageAnalyzer.alloc().init()
            req = self.VKCImageAnalyzerRequest.alloc().initWithImage_requestType_(self._preprocess(img), 1) #VKAnalysisTypeText
            req.setLocales_(['ja','en'])
            self.result = None
            analyzer.processRequest_progressHandler_completionHandler_(req, lambda progress: None, self._process)

            CFRunLoopRunInMode(kCFRunLoopDefaultMode, 10.0, False)

            if self.result == None:
                return (False, 'Unknown error!')
            return (True, self.result)

    def _process(self, analysis, error):
        res = ''
        lines = analysis.allLines()
        if lines:
            for line in lines:
                res += line.string() + '\n'
        self.result = res
        CFRunLoopStop(CFRunLoopGetCurrent())

    def _preprocess(self, img):
        image_bytes = pil_image_to_bytes(img, 'tiff')
        ns_data = NSData.dataWithBytes_length_(image_bytes, len(image_bytes))
        ns_image = NSImage.alloc().initWithData_(ns_data)
        return ns_image


class WinRTOCR:
    name = 'winrtocr'
    readable_name = 'WinRT OCR'
    key = 'w'
    available = False

    def __init__(self, config={}, lang='ja'):
        if sys.platform == 'win32':
            if int(platform.release()) < 10:
                logger.warning('WinRT OCR is not supported on Windows older than 10!')
            elif 'winocr' not in sys.modules:
                logger.warning('winocr not available, WinRT OCR will not work!')
            else:
                self.available = True
                logger.info('WinRT OCR ready')
        else:
            try:
                self.url = config['url']
                self.available = True
                logger.info('WinRT OCR ready')
            except:
                logger.warning('Error reading URL from config, WinRT OCR will not work!')

    def __call__(self, img, furigana_filter_sensitivity=0):
        img, is_path = input_to_pil_image(img)
        if not img:
            return (False, 'Invalid image provided')

        if sys.platform == 'win32':
            res = winocr.recognize_pil_sync(img, lang='ja')['text']
        else:
            params = {'lang': 'ja'}
            try:
                res = requests.post(self.url, params=params, data=self._preprocess(img), timeout=3)
            except requests.exceptions.Timeout:
                return (False, 'Request timeout!')
            except requests.exceptions.ConnectionError:
                return (False, 'Connection error!')

            if res.status_code != 200:
                return (False, 'Unknown error!')

            res = res.json()['text']

        x = (True, res)


        # img.close()
        return x

    def _preprocess(self, img):
        return pil_image_to_bytes(img, png_compression=1)

class OneOCR:
    name = 'oneocr'
    readable_name = 'OneOCR'
    key = 'z'
    available = False

    def __init__(self, config={}, lang='ja', get_furigana_sens_from_file=True):
        import regex
        self.initial_lang = lang
        self.regex = get_regex(lang)
        self.punctuation_regex = regex.compile(r'[\p{P}\p{S}]')
        self.get_furigana_sens_from_file = get_furigana_sens_from_file
        if sys.platform == 'win32':
            if int(platform.release()) < 10:
                logger.warning('OneOCR is not supported on Windows older than 10!')
            elif 'oneocr' not in sys.modules:
                logger.warning('oneocr not available, OneOCR will not work!')
            elif not os.path.exists(os.path.expanduser('~/.config/oneocr/oneocr.dll')):
                logger.warning('OneOCR DLLs not found, please install OwOCR Dependencies via OCR Tab in GSM.')
            else:
                try:
                    logger.info(f'Loading OneOCR model')
                    self.model = oneocr.OcrEngine()
                except RuntimeError as e:
                    logger.warning(e + ', OneOCR will not work!')
                else:
                    self.available = True
                    logger.info('OneOCR ready')
        else:
            try:
                self.url = config['url']
                self.available = True
                logger.info('OneOCR ready')
            except:
                logger.warning('Error reading URL from config, OneOCR will not work!')

    def get_regex(self, lang):
        if lang == "ja":
            self.regex = re.compile(r'[\u3041-\u3096\u30A1-\u30FA\u4E00-\u9FFF]')
        elif lang == "zh":
            self.regex = re.compile(r'[\u4E00-\u9FFF]')
        elif lang == "ko":
            self.regex = re.compile(r'[\uAC00-\uD7AF]')
        elif lang == "ar":
            self.regex = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
        elif lang == "ru":
            self.regex = re.compile(r'[\u0400-\u04FF\u0500-\u052F\u2DE0-\u2DFF\uA640-\uA69F\u1C80-\u1C8F]')
        elif lang == "el":
            self.regex = re.compile(r'[\u0370-\u03FF\u1F00-\u1FFF]')
        elif lang == "he":
            self.regex = re.compile(r'[\u0590-\u05FF\uFB1D-\uFB4F]')
        elif lang == "th":
            self.regex = re.compile(r'[\u0E00-\u0E7F]')
        else:
            self.regex = re.compile(
            r'[a-zA-Z\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u0250-\u02AF\u1D00-\u1D7F\u1D80-\u1DBF\u1E00-\u1EFF\u2C60-\u2C7F\uA720-\uA7FF\uAB30-\uAB6F]')

    def __call__(self, img, furigana_filter_sensitivity=0, return_coords=False, multiple_crop_coords=False, return_one_box=True, return_dict=False):
        lang = get_ocr_language()
        if self.get_furigana_sens_from_file:
            furigana_filter_sensitivity = get_furigana_filter_sensitivity()
        else:
            furigana_filter_sensitivity = furigana_filter_sensitivity
        if lang != self.initial_lang:
            self.initial_lang = lang
            self.regex = get_regex(lang)
        img, is_path = input_to_pil_image(img)
        if img.width < 51 or img.height < 51:
            new_width = max(img.width, 51)
            new_height = max(img.height, 51)
            new_img = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))
            new_img.paste(img, ((new_width - img.width) // 2, (new_height - img.height) // 2))
            img = new_img
        if not img:
            return (False, 'Invalid image provided')
        crop_coords = None
        crop_coords_list = []
        ocr_resp = ''
        if sys.platform == 'win32':
            try:
                ocr_resp = self.model.recognize_pil(img)
                if os.path.exists(os.path.expanduser("~/GSM/temp")):
                    with open(os.path.join(os.path.expanduser("~/GSM/temp"), 'oneocr_response.json'), 'w',
                                encoding='utf-8') as f:
                        json.dump(ocr_resp, f, indent=4, ensure_ascii=False)
                # print(json.dumps(ocr_resp))
                filtered_lines = [line for line in ocr_resp['lines'] if self.regex.search(line['text'])]
                x_coords = [line['bounding_rect'][f'x{i}'] for line in filtered_lines for i in range(1, 5)]
                y_coords = [line['bounding_rect'][f'y{i}'] for line in filtered_lines for i in range(1, 5)]
                if x_coords and y_coords:
                    crop_coords = (min(x_coords) - 5, min(y_coords) - 5, max(x_coords) + 5, max(y_coords) + 5)
                # logger.info(filtered_lines)
                res = ''
                skipped = []
                boxes = []
                if furigana_filter_sensitivity > 0:
                    passing_lines = []
                    for line in filtered_lines:
                        line_x1, line_x2, line_x3, line_x4 = line['bounding_rect']['x1'], line['bounding_rect']['x2'], \
                            line['bounding_rect']['x3'], line['bounding_rect']['x4']
                        line_y1, line_y2, line_y3, line_y4 = line['bounding_rect']['y1'], line['bounding_rect']['y2'], \
                            line['bounding_rect']['y3'], line['bounding_rect']['y4']
                        line_width = max(line_x2 - line_x1, line_x3 - line_x4)
                        line_height = max(line_y3 - line_y1, line_y4 - line_y2)
                        
                        # Check if the line passes the size filter
                        if line_width > furigana_filter_sensitivity and line_height > furigana_filter_sensitivity:
                            # Line passes - include all its text and add to passing_lines
                            for char in line['words']:
                                res += char['text']
                            passing_lines.append(line)
                        else:
                            # Line fails - only include punctuation, skip the rest
                            for char in line['words']:
                                skipped.extend(char for char in line['text'])
                        res += '\n'
                    filtered_lines = passing_lines
                    return_resp = {'text': res, 'text_angle': ocr_resp['text_angle'], 'lines': passing_lines}
                    # logger.info(
                    #     f"Skipped {len(skipped)} chars due to furigana filter sensitivity: {furigana_filter_sensitivity}")
                    # widths, heights = [], []
                    # for line in ocr_resp['lines']:
                    #     for word in line['words']:
                    #         if self.kana_kanji_regex.search(word['text']) is None:
                    #             continue
                    #         # x1, x2, x3, x4 = line['bounding_rect']['x1'], line['bounding_rect']['x2'], line['bounding_rect']['x3'], line['bounding_rect']['x4']
                    #         # y1, y2, y3, y4 = line['bounding_rect']['y1'], line['bounding_rect']['y2'], line['bounding_rect']['y3'], line['bounding_rect']['y4']
                    #         x1, x2, x3, x4 = word['bounding_rect']['x1'], word['bounding_rect']['x2'], \
                    #         word['bounding_rect']['x3'], word['bounding_rect']['x4']
                    #         y1, y2, y3, y4 = word['bounding_rect']['y1'], word['bounding_rect']['y2'], \
                    #         word['bounding_rect']['y3'], word['bounding_rect']['y4']
                    #         widths.append(max(x2 - x1, x3 - x4))
                    #         heights.append(max(y2 - y1, y3 - y4))
                    #
                    #
                    # max_width = max(sorted(widths)[:-max(1, len(widths) // 10)]) if len(widths) > 1 else 0
                    # max_height = max(sorted(heights)[:-max(1, len(heights) // 10)]) if len(heights) > 1 else 0
                    #
                    # required_width = max_width * furigana_filter_sensitivity
                    # required_height = max_height * furigana_filter_sensitivity
                    # for line in ocr_resp['lines']:
                    #     for word in line['words']:
                    #         x1, x2, x3, x4 = word['bounding_rect']['x1'], word['bounding_rect']['x2'], \
                    #         word['bounding_rect']['x3'], word['bounding_rect']['x4']
                    #         y1, y2, y3, y4 = word['bounding_rect']['y1'], word['bounding_rect']['y2'], \
                    #         word['bounding_rect']['y3'], word['bounding_rect']['y4']
                    #         width = max(x2 - x1, x3 - x4)
                    #         height = max(y2 - y1, y3 - y4)
                    #         if furigana_filter_sensitivity == 0 or width > required_width or height > required_height:
                    #             res += word['text']
                    #         else:
                    #             continue
                    #     res += '\n'
                else:
                    res = ocr_resp['text']
                    return_resp = ocr_resp
                    
                if multiple_crop_coords:
                    for line in filtered_lines:
                        crop_coords_list.append(
                            (line['bounding_rect']['x1'] - 5, line['bounding_rect']['y1'] - 5,
                             line['bounding_rect']['x3'] + 5, line['bounding_rect']['y3'] + 5))

            except RuntimeError as e:
                return (False, e)
        else:
            try:
                res = requests.post(self.url, data=self._preprocess(img), timeout=3)
            except requests.exceptions.Timeout:
                return (False, 'Request timeout!')
            except requests.exceptions.ConnectionError:
                return (False, 'Connection error!')

            if res.status_code != 200:
                return (False, 'Unknown error!')

            res = res.json()['text']

        x = [True, res]
        if return_coords:
            x.append(filtered_lines)
        if multiple_crop_coords:
            x.append(crop_coords_list)
        if return_one_box:
            x.append(crop_coords)
        if return_dict:
            x.append(return_resp)
        if is_path:
            img.close()
        return x

    def _preprocess(self, img):
        return pil_image_to_bytes(img, png_compression=1)

class AzureImageAnalysis:
    name = 'azure'
    readable_name = 'Azure Image Analysis'
    key = 'v'
    available = False

    def __init__(self, config={}, lang='ja'):
        if 'azure.ai.vision.imageanalysis' not in sys.modules:
            logger.warning('azure-ai-vision-imageanalysis not available, Azure Image Analysis will not work!')
        else:
            logger.info(f'Parsing Azure credentials')
            try:
                self.client = ImageAnalysisClient(config['endpoint'], AzureKeyCredential(config['api_key']))
                self.available = True
                logger.info('Azure Image Analysis ready')
            except:
                logger.warning('Error parsing Azure credentials, Azure Image Analysis will not work!')

    def __call__(self, img, furigana_filter_sensitivity=0):
        img, is_path = input_to_pil_image(img)
        if not img:
            return (False, 'Invalid image provided')

        try:
            read_result = self.client.analyze(image_data=self._preprocess(img), visual_features=[VisualFeatures.READ])
        except ServiceRequestError:
            return (False, 'Connection error!')
        except:
            return (False, 'Unknown error!')

        res = ''
        if read_result.read:
            for block in read_result.read.blocks:
                for line in block.lines:
                    res += line.text + '\n'
        else:
            return (False, 'Unknown error!')

        x = (True, res)

        # img.close()
        return x

    def _preprocess(self, img):
        if any(x < 50 for x in img.size):
            resize_factor = max(50 / img.width, 50 / img.height)
            new_w = int(img.width * resize_factor)
            new_h = int(img.height * resize_factor)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        return pil_image_to_bytes(img)

class EasyOCR:
    name = 'easyocr'
    readable_name = 'EasyOCR'
    key = 'e'
    available = False

    def __init__(self, config={'gpu': True}, lang='ja'):
        if 'easyocr' not in sys.modules:
            logger.warning('easyocr not available, EasyOCR will not work!')
        else:
            logger.info('Loading EasyOCR model')
            logging.getLogger('easyocr.easyocr').setLevel(logging.ERROR)
            self.model = easyocr.Reader(['ja','en'], gpu=config['gpu'])
            self.available = True
            logger.info('EasyOCR ready')

    def __call__(self, img, furigana_filter_sensitivity=0):
        img, is_path = input_to_pil_image(img)
        if not img:
            return (False, 'Invalid image provided')

        res = ''
        read_result = self.model.readtext(self._preprocess(img), detail=0)
        for text in read_result:
            res += text + '\n'

        x = (True, res)

        # img.close()
        return x

    def _preprocess(self, img):
        return pil_image_to_numpy_array(img)

class RapidOCR:
    name = 'rapidocr'
    readable_name = 'RapidOCR'
    key = 'r'
    available = False

    def __init__(self, lang='ja'):
        if 'rapidocr_onnxruntime' not in sys.modules:
            logger.warning('rapidocr_onnxruntime not available, RapidOCR will not work!')
        else:
            rapidocr_model_file = os.path.join(os.path.expanduser('~'),'.cache','rapidocr_japan_PP-OCRv4_rec_infer.onnx')
            if not os.path.isfile(rapidocr_model_file):
                logger.info('Downloading RapidOCR model ' + rapidocr_model_file)
                try:
                    cache_folder = os.path.join(os.path.expanduser('~'),'.cache')
                    if not os.path.isdir(cache_folder):
                        os.makedirs(cache_folder)
                    urllib.request.urlretrieve('https://github.com/AuroraWright/owocr/raw/master/rapidocr_japan_PP-OCRv4_rec_infer.onnx', rapidocr_model_file)
                except:
                    logger.warning('Download failed. RapidOCR will not work!')
                    return

            logger.info('Loading RapidOCR model')
            self.model = ROCR(rec_model_path=rapidocr_model_file)
            logging.getLogger().setLevel(logging.ERROR)
            self.available = True
            logger.info('RapidOCR ready')

    def __call__(self, img, furigana_filter_sensitivity=0):
        img, is_path = input_to_pil_image(img)
        if not img:
            return (False, 'Invalid image provided')

        res = ''
        read_results, elapsed = self.model(self._preprocess(img))
        if read_results:
            for read_result in read_results:
                res += read_result[1] + '\n'

        x = (True, res)

        # img.close()
        return x

    def _preprocess(self, img):
        return pil_image_to_numpy_array(img)

class OCRSpace:
    name = 'ocrspace'
    readable_name = 'OCRSpace'
    key = 'o'
    available = False

    def __init__(self, config={}, lang='ja'):
        try:
            self.api_key = config['api_key']
            self.max_byte_size = config.get('file_size_limit', 1000000)
            self.available = True
            logger.info('OCRSpace ready')
        except:
            logger.warning('Error reading API key from config, OCRSpace will not work!')

    def __call__(self, img, furigana_filter_sensitivity=0):
        img, is_path = input_to_pil_image(img)
        if not img:
            return (False, 'Invalid image provided')

        img_bytes, img_extension = self._preprocess(img)
        if not img_bytes:
            return (False, 'Image is too big!')

        data = {
            'apikey': self.api_key,
            'language': 'jpn'
        }
        files = {'file': ('image.' + img_extension, img_bytes, 'image/' + img_extension)}

        try:
            res = requests.post('https://api.ocr.space/parse/image', data=data, files=files, timeout=5)
        except requests.exceptions.Timeout:
            return (False, 'Request timeout!')
        except requests.exceptions.ConnectionError:
            return (False, 'Connection error!')

        if res.status_code != 200:
            return (False, 'Unknown error!')

        res = res.json()

        if isinstance(res, str):
            return (False, 'Unknown error!')
        if res['IsErroredOnProcessing']:
            return (False, res['ErrorMessage'])

        res = res['ParsedResults'][0]['ParsedText']
        x = (True, res)

        # img.close()
        return x

    def _preprocess(self, img):
        return limit_image_size(img, self.max_byte_size)


class GeminiOCR:
    name = 'gemini'
    readable_name = 'Gemini'
    key = ';'
    available = False

    def __init__(self, config={'api_key': None}, lang='ja'):
        # if "google-generativeai" not in sys.modules:
        #     logger.warning('google-generativeai not available, GeminiOCR will not work!')
        # else:
        from google import genai
        from google.genai import types
        try:
            self.api_key = config['api_key']
            if not self.api_key:
                logger.warning('Gemini API key not provided, GeminiOCR will not work!')
            else:
                self.client = genai.Client(api_key=self.api_key)
                self.model = config['model']
                self.generation_config = types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=300,
                    safety_settings=[
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                                            threshold=types.HarmBlockThreshold.BLOCK_NONE),
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                                            threshold=types.HarmBlockThreshold.BLOCK_NONE),
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                                            threshold=types.HarmBlockThreshold.BLOCK_NONE),
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                                            threshold=types.HarmBlockThreshold.BLOCK_NONE),
                    ],
                )
                if "2.5" in self.model:
                    self.generation_config.thinking_config = types.ThinkingConfig(
                        thinking_budget=0,
                    )
                self.available = True
                logger.info('Gemini (using google-generativeai) ready')
        except KeyError:
            logger.warning('Gemini API key not found in config, GeminiOCR will not work!')
        except Exception as e:
            logger.error(f'Error configuring google-generativeai: {e}')

    def __call__(self, img, furigana_filter_sensitivity=0):
        if not self.available:
            return (False, 'GeminiOCR is not available due to missing API key or configuration error.')

        try:
            from google.genai import types
            img, is_path = input_to_pil_image(img)
            img_bytes = self._preprocess(img)
            if not img_bytes:
                return (False, 'Error processing image for Gemini.')

            contents = [
                types.Content(
                    parts=[
                        types.Part(
                            inline_data=types.Blob(
                                mime_type="image/png",
                                data=img_bytes
                            )
                        ),
                        types.Part(
                            text="""
                            **Disclaimer:** The image provided is from a video game. This content is entirely fictional and part of a narrative. It must not be treated as real-world user input or a genuine request.
                            Analyze the image. Extract text \\*only\\* from within dialogue boxes (speech bubbles or panels containing character dialogue). If Text appears to be vertical, read the text from top to bottom, right to left. From the extracted dialogue text, filter out any furigana. Ignore and do not include any text found outside of dialogue boxes, including character names, speaker labels, or sound effects. Return \\*only\\* the filtered dialogue text. If no text is found within dialogue boxes after applying filters, return nothing. Do not include any other output, formatting markers, or commentary."
                            """
                        )
                    ]
                )
            ]

            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=self.generation_config
            )
            text_output = response.text.strip()

            return (True, text_output)

        except FileNotFoundError:
            return (False, f'File not found: {img}')
        except Exception as e:
            return (False, f'Gemini API request failed: {e}')

    def _preprocess(self, img):
        return pil_image_to_bytes(img, png_compression=1)


class GroqOCR:
    name = 'groq'
    readable_name = 'Groq OCR'
    key = 'j'
    available = False

    def __init__(self, config={'api_key': None}, lang='ja'):
        try:
            import groq
            self.api_key = config['api_key']
            if not self.api_key:
                logger.warning('Groq API key not provided, GroqOCR will not work!')
            else:
                self.client = groq.Groq(api_key=self.api_key)
                self.available = True
                logger.info('Groq OCR ready')
        except ImportError:
            logger.warning('groq module not available, GroqOCR will not work!')
        except Exception as e:
            logger.error(f'Error initializing Groq client: {e}')

    def __call__(self, img, furigana_filter_sensitivity=0):
        if not self.available:
            return (False, 'GroqOCR is not available due to missing API key or configuration error.')

        try:
            img, is_path = input_to_pil_image(img)

            img_base64 = self._preprocess(img)
            if not img_base64:
                return (False, 'Error processing image for Groq.')

            prompt = (
                "Analyze the image. Extract text *only* from within dialogue boxes (speech bubbles or panels containing character dialogue). If Text appears to be vertical, read the text from top to bottom, right to left. From the extracted dialogue text, filter out any furigana. Ignore and do not include any text found outside of dialogue boxes, including character names, speaker labels, or sound effects. Return *only* the filtered dialogue text. If no text is found within dialogue boxes after applying filters, return nothing. Do not include any other output, formatting markers, or commentary."
                # "Analyze this i#mage and extract text from it"
                # "(speech bubbles or panels containing character dialogue). From the extracted dialogue text, "
                # "filter out any furigana. Ignore and do not include any text found outside of dialogue boxes, "
                # "including character names, speaker labels, or sound effects. Return *only* the filtered dialogue text. "
                # "If no text is found within dialogue boxes after applying filters, return an empty string. "
                # "OR, if there are no text bubbles or dialogue boxes found, return everything."
                # "Do not include any other output, formatting markers, or commentary, only the text from the image."
            )

            response = self.client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}},
                        ],
                    }
                ],
                max_tokens=300,
                temperature=0.0
            )

            if response.choices and response.choices[0].message.content:
                text_output = response.choices[0].message.content.strip()
                return (True, text_output)
            else:
                return (True, "")

        except FileNotFoundError:
            return (False, f'File not found: {img}')
        except Exception as e:
            return (False, f'Groq API request failed: {e}')

    def _preprocess(self, img):
        return base64.b64encode(pil_image_to_bytes(img, png_compression=1)).decode('utf-8')


# OpenAI-Compatible Endpoint OCR using LM Studio 
class localLLMOCR:
    name= 'local_llm_ocr'
    readable_name = 'Local LLM OCR'
    key = 'a'
    available = False
    last_ocr_time = time.time() - 5

    def __init__(self, config={}, lang='ja'):
        self.keep_llm_hot_thread = None
        # All three config values are required: url, model, api_key
        if not config or not (config.get('url') and config.get('model') and config.get('api_key')):
            logger.warning('Local LLM OCR requires url, model, and api_key in config, Local LLM OCR will not work!')
            return

        try:
            import openai
        except ImportError:
            logger.warning('openai module not available, Local LLM OCR will not work!')
            return
        import openai, threading
        try:
            self.api_url = config.get('url', 'http://localhost:1234/v1/chat/completions')
            self.model = config.get('model', 'qwen2.5-vl-3b-instruct')
            self.api_key = config.get('api_key', 'lm-studio')
            self.keep_warm = config.get('keep_warm', True)
            self.custom_prompt = config.get('prompt', None)
            self.available = True
            if not self.check_url_for_connectivity(self.api_url):
                self.available = False
                logger.warning(f'Local LLM OCR API URL not reachable: {self.api_url}')
                return
            self.client = openai.OpenAI(
                base_url=self.api_url.replace('/v1/chat/completions', '/v1'),
                api_key=self.api_key,
                timeout=1
            )
            if self.client.models.retrieve(self.model):
                self.model = self.model
            logger.info(f'Local LLM OCR (OpenAI-compatible) ready with model {self.model}')
            if self.keep_warm:
                self.keep_llm_hot_thread = threading.Thread(target=self.keep_llm_warm, daemon=True)
                self.keep_llm_hot_thread.start()
        except Exception as e:
            logger.warning(f'Error initializing Local LLM OCR, Local LLM OCR will not work!')
            
    def check_url_for_connectivity(self, url):
        import requests
        try:
            response = requests.get(url, timeout=0.5)
            return response.status_code == 200
        except Exception:
            return False

    def keep_llm_warm(self):
        def ocr_blank_black_image():
            if self.last_ocr_time and (time.time() - self.last_ocr_time) < 5:
                return
            import numpy as np
            from PIL import Image
            # Create a blank black image
            blank_image = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
            logger.info('Keeping local LLM OCR warm with a blank black image')
            self(blank_image)
        
        while True:
            ocr_blank_black_image()
            time.sleep(5)

    def __call__(self, img, furigana_filter_sensitivity=0):
        import base64
        try:
            img, is_path = input_to_pil_image(img)
            img_bytes = pil_image_to_bytes(img)
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            if self.custom_prompt and self.custom_prompt.strip() != "":
                prompt = self.custom_prompt.strip()
            else:
                prompt = f"""
                Extract all {CommonLanguages.from_code(get_ocr_language()).name} Text from Image. Ignore all Furigana. Do not return any commentary, just the text in the image. Do not Translate. If there is no text in the image, return "" (Empty String).
                """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}},
                        ],
                    }
                ],
                max_tokens=4096,
                temperature=0.1
            )
            self.last_ocr_time = time.time()
            if response.choices and response.choices[0].message.content:
                text_output = response.choices[0].message.content.strip()
                return (True, text_output)
            else:
                return (True, "")
        except Exception as e:
            return (False, f'Local LLM OCR request failed: {e}')

# class QWENOCR:
#     name = 'qwenv2'
#     readable_name = 'Qwen2-VL'
#     key = 'q'
    
#     # Class-level attributes for model and processor to ensure they are loaded only once
#     model = None
#     processor = None
#     device = None
#     available = False

#     @classmethod
#     def initialize(cls):
#         import torch
#         from transformers import AutoModelForImageTextToText, AutoProcessor
#         """
#         Class method to initialize the model. Call this once at the start of your application.
#         This prevents reloading the model on every instantiation.
#         """
#         if cls.model is not None:
#             logger.info('Qwen2-VL is already initialized.')
#             return

#         try:
#             if not torch.cuda.is_available():
#                 logger.warning("CUDA not available, Qwen2-VL will run on CPU, which will be very slow.")
#                 # You might want to prevent initialization on CPU entirely
#                 # raise RuntimeError("CUDA is required for efficient Qwen2-VL operation.")
            
#             cls.device = "cuda" if torch.cuda.is_available() else "cpu"
            
#             cls.model = AutoModelForImageTextToText.from_pretrained(
#                 "Qwen/Qwen2-VL-2B-Instruct", 
#                 torch_dtype="auto", # Uses bfloat16/float16 if available, which is faster
#                 device_map=cls.device
#             )
#             # For PyTorch 2.0+, torch.compile can significantly speed up inference after a warm-up call
#             # cls.model = torch.compile(cls.model) 
            
#             cls.processor = AutoProcessor.from_pretrained(
#                 "Qwen/Qwen2-VL-2B-Instruct", 
#                 use_fast=True
#             )
            
#             cls.available = True
            
#             conversation = [
#                 {
#                     "role": "user",
#                     "content": [
#                         {"type": "image"},
#                         {"type": "text", "text": "Extract all the text from this image, ignore all furigana."},
#                     ],
#                 }
#             ]
            
#             # The same prompt is applied to all images in the batch
#             cls.text_prompt = cls.processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
#             logger.info(f'Qwen2.5-VL ready on device: {cls.device}')
#         except Exception as e:
#             logger.warning(f'Qwen2-VL not available: {e}')
#             cls.available = False

#     def __init__(self, config={}, lang='ja'):
#         # The __init__ is now very lightweight. It just checks if initialization has happened.
#         if not self.available:
#             raise RuntimeError("QWENOCR has not been initialized. Call QWENOCR.initialize() first.")

#     def __call__(self, images):
#         """
#         Processes a single image or a list of images.
#         :param images: A single image (path or PIL.Image) or a list of images.
#         :return: A tuple (success, list_of_results)
#         """
#         if not self.available:
#             return (False, ['Qwen2-VL is not available.'])
            
#         try:
#             # Standardize input to be a list
#             if not isinstance(images, list):
#                 images = [images]

#             pil_images = [input_to_pil_image(img)[0] for img in images]
            
#             # The processor handles batching of images and text prompts
#             inputs = self.processor(
#                 text=[self.text_prompt] * len(pil_images), 
#                 images=pil_images, 
#                 padding=True, 
#                 return_tensors="pt"
#             ).to(self.device)

#             output_ids = self.model.generate(**inputs, max_new_tokens=32)

#             # The decoding logic needs to be slightly adjusted for batching
#             input_ids_len = [len(x) for x in inputs.input_ids]
#             generated_ids = [
#                 output_ids[i][input_ids_len[i]:] for i in range(len(input_ids_len))
#             ]

#             output_text = self.processor.batch_decode(
#                 generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True
#             )
            
#             return (True, output_text)
#         except Exception as e:
#             return (False, [f'Qwen2-VL inference failed: {e}'])


# QWENOCR.initialize()
# qwenocr = QWENOCR()

# localOCR = localLLMOCR(config={'api_url': 'http://localhost:1234/v1/chat/completions', 'model': 'qwen2.5-vl-3b-instruct'})

# for i in range(10):
#     start_time = time.time()
#     res, text = localOCR(Image.open(r"C:\Users\Beangate\GSM\GameSentenceMiner\GameSentenceMiner\owocr\owocr\test_furigana.png"))  # Example usage
#     end_time = time.time()

#     print(f"Time taken: {end_time - start_time:.2f} seconds")
#     print(text)
# class LocalOCR:
#     name = 'local_ocr'
#     readable_name = 'Local OCR'
#     key = '-'
#     available = False
#
#     def __init__(self, lang='ja'):
#         self.requests_session = requests.Session()
#         self.available = True
#         # logger.info('Local OCR ready') # Uncomment if you have a logger defined
#
#     def __call__(self, img, furigana_filter_sensitivity=0):
#         if not isinstance(img, Image.Image):
#             try:
#                 img = Image.open(io.BytesIO(img))
#             except Exception:
#                 return (False, 'Invalid image provided')
#
#         img = input_to_pil_image(img)
#
#         img_base64 = self._preprocess(img)
#         if not img_base64:
#             return (False, 'Image preprocessing failed (e.g., too big after resize)!')
#
#         api_url = 'http://localhost:2333/api/ocr'
#         # Send as JSON with base64 encoded image
#         json_data = {
#             'image': img_base64
#         }
#
#         try:
#             res = self.requests_session.post(api_url, json=json_data, timeout=5)
#             print(res.content)
#         except requests.exceptions.Timeout:
#             return (False, 'Request timeout!')
#         except requests.exceptions.ConnectionError:
#             return (False, 'Connection error!')
#
#         if res.status_code != 200:
#             return (False, f'Error: {res.status_code} - {res.text}')
#
#         try:
#             data = res.json()
#             # Assuming the local OCR service returns text in a 'text' key
#             extracted_text = data.get('text', '')
#             return (True, extracted_text)
#         except requests.exceptions.JSONDecodeError:
#             return (False, 'Invalid JSON response from OCR service!')
#
#     def _preprocess(self, img):
#         return base64.b64encode(pil_image_to_bytes(img, png_compression=1)).decode('utf-8')

# lens = GeminiOCR(config={'model': 'gemini-2.5-flash-lite-preview-06-17', 'api_key': ''})
#
# res, text = lens(Image.open('test_furigana.png'))  # Example usage
#
# print(text)