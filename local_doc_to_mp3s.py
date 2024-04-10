import time
import base64
from concurrent.futures import ThreadPoolExecutor

import requests
from pedalboard.io import AudioFile

INPUT_FILE = 'deleteme.txt'
N_WORKERS = 1

# split document into paragraphs
doc = [x for x in map(str.strip, open(INPUT_FILE).read().split('\n')) if x][:5]
N = len(str(len(doc)))

def base64_to_mp3(encoded, outfile):
    file_content=base64.b64decode(encoded)
    with open(outfile, "wb") as f:
        f.write(file_content)

def worker(enumerated_text, prefix='results/deleteme', N=N, kwargs=None):
    kwargs = kwargs or {}
    n, text = enumerated_text


    fname = f"{prefix}_{n:0{N}}.mp3"
    print(n, fname)
    data = {'text': text}
    response = requests.post("http://localhost:8000/runsync", json={'input': data})
    J = response.json()
    success = J['status'] == 'COMPLETED'
    if success:
        base64_to_mp3(J['output'], fname)
        outfile=fname
        duration = AudioFile(fname).duration

    else:
        outfile=None
        durantion=0

    return {'index': n, 'success': success, 'duration': duration, 'text': text, 'file_name': outfile}

if __name__ == '__main__':
    start = time.time()
    with ThreadPoolExecutor(max_workers=N_WORKERS) as pool:
        result = pool.map(worker, enumerate(doc))
    print(f"done in {time.time()-start}")
# 
# # associate the words with timestamps for making a video
# durations = []
# for i, words in enumerate(doc):
#     fname = f"deleteme{i:03}.wav"
#     audio = pydub.AudioSegment.from_file(fname)
#     durations.append((audio.duration_seconds, words))
