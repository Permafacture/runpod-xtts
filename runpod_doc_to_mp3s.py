import time
from pathlib import Path
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import uuid

from tqdm import tqdm
from pedalboard.io import AudioFile
import runpod
import pysbd


# config
#########

API_KEY = "Get UR Own From Runpod"
ENDPOINT_ID = "ID of serverless instance"
WORK_DIR = 'project_1'
CHECK_LENGTH = 250  # Alert if any sentences are too long and abort. False means don't check
DOCUMENT = Path(WORK_DIR, 'document.txt')
STATUS_CSV = Path(WORK_DIR, 'status.csv')
OUTFILE = Path(WORK_DIR, 'FinalAudio.mp3')
N_WORKERS = 4  # same as runpod serverless `max workers`
LANGUAGE = 'en'


# code
#######

runpod.api_key = API_KEY
endpoint = runpod.Endpoint(ENDPOINT_ID)

def check_len(doc, max_length=CHECK_LENGTH):
    segmenter = pysbd.Segmenter(language=LANGUAGE, clean=True) 
    sentences = [S for P in doc for S in segmenter.segment(P)]
    too_long = [S for S in sentences if len(S) > max_length]
    if too_long:
        out = '\n\n'.join(too_long)
        out = "the following sentences are longer than {max_length}:\n\n" + out
        raise RuntimeError(f"{out}\n\nSet CHECK_LENGTH to False if you don't want this check")


def init_csv(input_file, status_csv, max_length=CHECK_LENGTH):
    # split document into paragraphs
    if status_csv.exists():
        raise RuntimeError(f"{status_csv} exists")
    doc = [x for x in map(str.strip, open(input_file).read().split('\n')) if x]
    if CHECK_LENGTH:
        check_len(doc, max_length=max_length)
    rows = []
    for i, text in enumerate(doc):
        row = {'index': i, 'success': None, 'duration': None, 'text': text,
            'response_time': None, 'filename': None}
        rows.append(row)
    with open(status_csv, 'w') as fh:
        writer = csv.DictWriter(fh, fieldnames=row.keys())
        writer.writeheader()
        writer.writerows(rows)

def base64_to_mp3(encoded, outfile):
    file_content=base64.b64decode(encoded)
    with open(outfile, "wb") as f:
        f.write(file_content)

def exception_to_row(f):
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            print("args:", args)
            row = args[0]
            print(f"exception on item {row['index']}")
            print(e)
            return row
    return wrapper

@exception_to_row
def worker(row, workdir=WORK_DIR, kwargs=None):
    kwargs = kwargs or {}
    n = row['index']
    text = row['text']


    unique = str(uuid.uuid4())[:10]  # extremely likely to be unique
    fname = str(Path(workdir, f"z{unique}.mp3"))
    data = {'text': text,
            'speaker': "Ana Florence",
            'language': "en"}
    data.update(**kwargs)  # overwrite defaults if kwargs is provided

    start = time.time()
    response = endpoint.run_sync({"input": data}, timeout=600)
    response_time = time.time() - start
    success = len(response) > 20
    if success:
        base64_to_mp3(response, fname)
        outfile = fname
        duration = AudioFile(fname).duration

    else:
        outfile = None
        duration = 0
        success = response

    return {'index': n, 'success': str(success), 'duration': duration, 'text': text,
            'response_time': response_time, 'filename': outfile}

def compile_final_audio(rows, outfile):
    rows = [row for row in rows if row['success'] == 'True' and row['index']]
    assert rows, "Expected some passing items"
    rows.sort(key = lambda x: int(x['index']))
    with AudioFile(str(rows[0]['filename'])) as f:
        samplerate = f.samplerate
        num_channels = f.num_channels

    with AudioFile(str(outfile), 'w', samplerate, num_channels) as of:
        for row in rows:
            with AudioFile(row['filename']) as f:
                while f.tell() < f.frames:
                    chunk = f.read(f.samplerate)
                    of.write(chunk)

if __name__ == '__main__':
    start = time.time()
    if not STATUS_CSV.exists():
        print(f"Creating {STATUS_CSV}")
        init_csv(DOCUMENT, STATUS_CSV)
    rows = list(csv.DictReader(open(STATUS_CSV)))
    rows = [row for row in rows if row['index']] # user might introduce empty rows in excel
    good_rows = [row for row in rows if row['success'] == 'True']
    incomplete = [row for row in rows if row['success'] != 'True']
    N = len(incomplete)
    print(f"Processing {N} items")

    try:
        with ThreadPoolExecutor(max_workers=5) as executor, tqdm(total=N) as pbar:
            futures = [executor.submit(worker, item) for item in incomplete]
            for future in as_completed(futures):
                good_rows.append(future.result())
                pbar.update(1)
    finally:
        # if something happens, at least record the progress that has been made
        all_rows = good_rows.copy()
        good_ids = {row['index'] for row in all_rows}
        for row in incomplete:
            if row['index'] not in good_ids:
                all_rows.append(row)
        all_rows.sort(key = lambda x: int(x['index']))
        with open(STATUS_CSV, 'w') as fh:
            writer = csv.DictWriter(fh, fieldnames=all_rows[0].keys())
            writer.writeheader()
            writer.writerows(all_rows)

    rows = list(csv.DictReader(open(STATUS_CSV)))
    print(f"compiling final output in {OUTFILE}")
    compile_final_audio(rows, OUTFILE)






# 
# # associate the words with timestamps for making a video
# durations = []
# for i, words in enumerate(doc):
#     fname = f"deleteme{i:03}.wav"
#     audio = pydub.AudioSegment.from_file(fname)
#     durations.append((audio.duration_seconds, words))
