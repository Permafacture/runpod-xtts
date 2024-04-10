""" Example handler file. """
import tempfile
import runpod
from TTS.api import TTS
from pedalboard.io import AudioFile
import base64

# If your handler runs inference on a model, load the model here.
# You will want models to be loaded into memory before starting serverless.

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)

def wav_to_mp3(wavfile, outfile):
    with AudioFile(wavfile) as f:
        with AudioFile(outfile, 'w', f.samplerate, f.num_channels) as o:
            while f.tell() < f.frames:
                chunk = f.read(f.samplerate)
                o.write(chunk)

def handler(job):
    """ Handler function that will be used to process jobs. """
    job_input = job['input']
    
    tmpdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)

    wav_file = f"{tmpdir.name}/deleteme.wav"
    mp3_file = f"{tmpdir.name}/deleteme.mp3"

    tts.tts_to_file(text=job_input['text'],
                    file_path=wav_file,
                    speaker=job_input.get("speaker", "Ana Florence"),
                    language=job_input.get("language", "en"),
                    split_sentences=job_input.get("split_sentences", True)
                    )
    wav_to_mp3(wav_file, mp3_file)

    return base64.b64encode(open(mp3_file, 'rb').read()).decode('utf-8')

runpod.serverless.start({"handler": handler})
