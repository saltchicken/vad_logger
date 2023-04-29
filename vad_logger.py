import pyaudio
import webrtcvad
import wave
from datetime import datetime
from collections import deque

class VAD_Logger():

    def __init__(self, output_path, channels=1, rate=16000):
        self.output_path = output_path
        self.channels = channels
        self.rate = rate
        self.format = pyaudio.paInt16
        self.chunk_size = 320 # 20ms
        self._pa = pyaudio.PyAudio()
        self._stream = self._pa.open(format=self.format,
                                     channels=self.channels,
                                     rate=self.rate,
                                     input=True,
                                     frames_per_buffer=self.chunk_size)
        self.frames = []
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(3)
        self.is_speaking = False
        self.not_speaking_frames_count = 0
        self.speaking_frames_count = 0
        self.proceed = True
        self.buffer = deque('', 5)
        for _ in range(5):
            audio_data = self._stream.read(self.chunk_size)
            is_speech = self.vad.is_speech(audio_data, self.rate)
            # print(is_speech)

    def start_recording(self):
        print('Begin recording...')
        try:
            while True:
                audio_data = self._stream.read(self.chunk_size)
                self.buffer.append(audio_data)
                is_speech = self.vad.is_speech(audio_data, self.rate)
                if is_speech:
                    self.speaking_frames_count += 1
                    self.not_speaking_frames_count = 0
                else:
                    self.not_speaking_frames_count += 1
                    self.speaking_frames_count = 0

                if self.speaking_frames_count > 3:
                    self.is_speaking = True
                    if len(self.frames) == 0:
                        self.frames = self.frames + list(self.buffer)
                
                if self.not_speaking_frames_count > 5:
                    self.is_speaking = False

                if self.is_speaking:
                    self.frames.append(audio_data)
                else:
                    if len(self.frames) > 5:
                        filename = ''.join([self.output_path, '/clip-', datetime.utcnow().strftime('%Y%m%d%H%M%S'), '.wav'])
                        wf = wave.open(filename, "wb")
                        wf.setnchannels(self.channels)
                        wf.setsampwidth(self._pa.get_sample_size(self.format))
                        wf.setframerate(self.rate)
                        wf.writeframes(b''.join(self.frames))
                        wf.close()
                        self.frames = []
                        return filename
                    else:
                        self.frames = []
                        
        except KeyboardInterrupt as e:
            print('Terminating recording...', end='')
            return None