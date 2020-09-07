import xml
import httplib2
import uuid
from config import YANDEX_ASR_KEY
from testset import readchunks
from testset import convert_byte
from testset.testerorr.speecherorr import SpeechException

YANDEX_ASR_HOST = 'asr.yandex.net'
YANDEX_PATH = '/asr_xml'
CHUNK_SIZE = 1024 ** 2


def speech_to_text(filename=None, bytes=None, request_id=uuid.uuid4().hex, topic='notes', lang='ru-RU',
                   key=YANDEX_API_KEY):

    if filename:
        with open(filename, 'br') as file:
            bytes = file.read()
    if not bytes:
        raise Exception('Neither file name nor bytes provided.')

    bytes = convert_byte.convert_to_pcm16b16000r(in_bytes=bytes)

    url = YANDEX_PATH + '?uuid=%s&key=%s&topic=%s&lang=%s' % (
        request_id,
        key,
        topic,
        lang)

    chunks = readchunks.read_chunks(CHUNK_SIZE, bytes)

    connection = httplib2.HTTPConnectionWithTimeout(YANDEX_ASR_HOST)

    connection.connect()
    connection.putrequest('POST', url)
    connection.putheader('Transfer-Encoding', 'chunked')
    connection.putheader('Content-Type', 'audio/x-pcm;bit=16;rate=16000')
    connection.endheaders()

    for chunk in chunks:
        connection.send(('%s\r\n' % hex(len(chunk))[2:]).encode())
        connection.send(chunk)
        connection.send('\r\n'.encode())

    connection.send('0\r\n\r\n'.encode())
    response = connection.getresponse()

    if response.code == 200:
        response_text = response.read()
        xml = xml.etree.ElementTree.fromstring(response_text)

        if int(xml.attrib['success']) == 1:
            max_confidence = - float("inf")
            text = ''

            for child in xml:
                if float(child.attrib['confidence']) > max_confidence:
                    text = child.text
                    max_confidence = float(child.attrib['confidence'])

            if max_confidence != - float("inf"):
                return text
            else:

                raise SpeechException(
                    'No text found.\n\nResponse:\n%s' % (response_text))
        else:
            raise SpeechException(
                'No text found.\n\nResponse:\n%s' % (response_text))
    else:
        raise SpeechException('Unknown error.\nCode: %s\n\n%s' %
                              (response.code, response.read()))

