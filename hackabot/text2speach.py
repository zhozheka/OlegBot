import sys
sys.path.append('/Users/e-zholkovskiy/Yandex.Disk.localized/skoltech/term5/hack/tinkoff1/voicekit-examples/python')

from tinkoff.cloud.tts.v1 import tts_pb2_grpc, tts_pb2
from auth import authorization_metadata
import grpc
import os
import wave
import ffmpeg
import time


endpoint = "tts.tinkoff.ru:443"
api_key = "ZXZ4ZmZxbXhjZndkZXN4YnB4c3B1dnFrbWRla2ZxZWw=s.chekulaevatinkoff"
secret_key = "YmNobHphZWZrb3dybHF1YnhxZmR5emtoZXZ3ZmlxcXI="

sample_rate = 48000


def build_request(text):
    return tts_pb2.SynthesizeSpeechRequest(
        input=tts_pb2.SynthesisInput(
            text=text),
        audio_config=tts_pb2.AudioConfig(
            audio_encoding=tts_pb2.LINEAR16,
            sample_rate_hertz=sample_rate,
        ),
    )

def text2speach(text, tmp_dir='./tmp'):
    ts = int(time.time() * 10**6)
    wav_tmp = os.path.join(tmp_dir, '{}.wav'.format(ts))
    oga_tmp = os.path.join(tmp_dir, '{}.oga'.format(ts))

    with wave.open(wav_tmp, "wb") as f:
        f.setframerate(sample_rate)
        f.setnchannels(1)
        f.setsampwidth(2)

        stub = tts_pb2_grpc.TextToSpeechStub(grpc.secure_channel(endpoint, grpc.ssl_channel_credentials()))
        request = build_request(text)
        metadata = authorization_metadata(api_key, secret_key, "tinkoff.cloud.tts")
        responses = stub.StreamingSynthesize(request, metadata=metadata)
        # for key, value in responses.initial_metadata():
        #     if key == "x-audio-num-samples":
        #         #print("Estimated audio duration is " + str(int(value) / sample_rate) + " seconds")
        #         break
        for stream_response in responses:
            f.writeframes(stream_response.audio_chunk)

    stream = ffmpeg.input(wav_tmp)
    stream = ffmpeg.output(stream, oga_tmp)
    ffmpeg.run(stream, overwrite_output=True)
    with open(oga_tmp, 'rb') as f:
        fp = f.read()
    os.remove(oga_tmp)
    os.remove(wav_tmp)
    return fp
