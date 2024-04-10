This is a worker for a runpod serverless instance to turn text into speech using xTTS

The runpod_doc_to_mp3.py script chunks a text file into paragraphs to be sent to
a runpod instance. The individual responses are collected and compiled into one 
final Mp3. Status is tracked ina csv so the process can be stopped and resumed.
Or if some audio is bad, those clips can be reprocessed and the text for those
clips can be edited.

local_doc_to_mp3.py is for testing lcoally during development on a machine
with a GPU. It requires changing a line in the xtts-worker Dockerfile and
probably doesn't support multiple workers.

to install
    `pip install -r requirements.txt`
    add API key and endpoint ID to runpod_doc_to_mp3.py
    create a folder, add text file to it, and adjust config in runpod_doc_to_mp3.py

Additional tts working directories can live side by side, just change the config


To create your own runpod serverless instance:

    * The cheapest GPU is fine
    * No active workers
    * Max workers is however many threads you intend to run at once
    * 1 GPU per worker
    * 5 second idel timeout is fine
    * Flashboot is fine
    * execution timeout can be like 300 seconds. It only takes ~20 seconds to start form cold boot
          and processing one normal paragraph is about 70 seconds
    * Container image is elbiot/runpod-tts:0.1.1
    * 5 GB container disk is fine. I'm very little is used
    * No environment variables of advanced options necessary
    * If trying to limit data center location, make sure the GPU you want is still available
        after limiting this


