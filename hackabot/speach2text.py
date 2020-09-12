import sys
sys.path.append("..")
sys.path.append('/Users/e-zholkovskiy/Yandex.Disk.localized/skoltech/term5/hack/tinkoff1/voicekit-examples/python')

from tinkoff.cloud.stt.v1 import stt_pb2_grpc, stt_pb2
from auth import authorization_metadata
import grpc
import os
import wave
from urllib.request import urlopen
import time
import ffmpeg


endpoint = os.environ.get("VOICEKIT_ENDPOINT") or "stt.tinkoff.ru:443"
api_key = "ZXZ4ZmZxbXhjZndkZXN4YnB4c3B1dnFrbWRla2ZxZWw=s.chekulaevatinkoff"
secret_key = "YmNobHphZWZrb3dybHF1YnhxZmR5emtoZXZ3ZmlxcXI="


def build_first_request(sample_rate_hertz, num_channels):
    request = stt_pb2.StreamingRecognizeRequest()
    request.streaming_config.config.encoding = stt_pb2.AudioEncoding.LINEAR16
    request.streaming_config.config.sample_rate_hertz = sample_rate_hertz
    request.streaming_config.config.num_channels = num_channels
    return request


def generate_requests(path):
    try:
        with wave.open(path) as f:
            yield build_first_request(f.getframerate(), f.getnchannels())
            frame_samples = f.getframerate()//10 # Send 100ms at a time
            for data in iter(lambda:f.readframes(frame_samples), b''):
                request = stt_pb2.StreamingRecognizeRequest()
                request.audio_content = data
                yield request
    except Exception as e:
        print("Got exception in generate_requests", e)
        raise


def print_streaming_recognition_responses(responses):
    for response in responses:
        for result in response.results:
            print("Channel", result.recognition_result.channel)
            print("Phrase start:", result.recognition_result.start_time.ToTimedelta())
            print("Phrase end:  ", result.recognition_result.end_time.ToTimedelta())
            for alternative in result.recognition_result.alternatives:
                print('"' + alternative.transcript + '"')
            print("------------------")


def speach2text(url, tmp_dir='./tmp'):
    ts = int(time.time() * 10**6)
    wav_tmp = os.path.join(tmp_dir, '{}.wav'.format(ts))
    oga_tmp = os.path.join(tmp_dir, '{}.oga'.format(ts))

    r = urlopen(url)

    with open(oga_tmp, 'wb') as f:
        f.write(r.read())

    stream = ffmpeg.input(oga_tmp)
    stream = ffmpeg.output(stream, wav_tmp)
    ffmpeg.run(stream, overwrite_output=True)


    stub = stt_pb2_grpc.SpeechToTextStub(grpc.secure_channel(endpoint, grpc.ssl_channel_credentials()))
    metadata = authorization_metadata(api_key, secret_key, "tinkoff.cloud.stt")
    responses = stub.StreamingRecognize(generate_requests(wav_tmp), metadata=metadata)
    text = next(responses).results[0].recognition_result.alternatives[0].transcript
    os.remove(wav_tmp)
    os.remove(oga_tmp)
    return text
