import sys
import queue
import threading
import pythoncom
import win32com.client
import textwrap # New import

# --- Constants for queue actions ---
_ACTION_SPEAK = 0
_ACTION_STOP_SILENT = 2 # To explicitly stop without speaking anything new.
_ACTION_SET_RATE = 3
_ACTION_SHUTDOWN = 4

_CHUNK_SIZE = 200 # Max characters per chunk. SAPI is fine with larger but this helps responsiveness.

class Speaker:
    """
    A thread-safe class that handles all text-to-speech operations on Windows
    using the SAPI5 COM interface. It isolates the COM object to a single
    dedicated thread to prevent common threading issues.
    """
    def __init__(self):
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._worker)
        self.thread.daemon = True
        self.rate = 130 # Store rate in WPM
        self._is_speaking_flag = threading.Event()
        self.thread.start()

    def _wpm_to_sapi_rate(self, wpm):
        """Converts words-per-minute (approx) to SAPI's -10 to 10 scale."""
        return max(-10, min(10, int((wpm - 150) / 10)))

    def _worker(self):
        """The single worker thread that owns the SAPI voice object."""
        pythoncom.CoInitialize()
        try:
            voice = win32com.client.Dispatch("SAPI.SpVoice")
            voice.Rate = self._wpm_to_sapi_rate(self.rate)
            while True:
                try:
                    action, payload = self.queue.get(timeout=0.1)
                    
                    if action == _ACTION_SHUTDOWN:
                        break
                    
                    if action == _ACTION_SPEAK:
                        text = payload
                        voice.Speak(text, 0) # Speak asynchronously, don't purge
                    elif action == _ACTION_STOP_SILENT:
                        # Speak empty string with purge to stop any current speech
                        voice.Speak("", 1) 
                    elif action == _ACTION_SET_RATE:
                        # Payload is XML rate command
                        voice.Speak(payload, 0) # Speak XML rate command
                    
                    self.queue.task_done()

                except queue.Empty:
                    # This is the main path when no new text is queued.
                    # We use the timeout to periodically check the speaking status.
                    pass
                except Exception as e:
                    # Catch any exceptions during speak/rate calls, but keep worker alive.
                    # print(f"Error in SAPI worker: {e}")
                    pass

                # Check SAPI status to update our flag
                # SRSEDone = 1, SRSEIsSpeaking = 2
                if voice.Status.RunningState == 2:
                    self._is_speaking_flag.set()
                else:
                    self._is_speaking_flag.clear()

        finally:
            pythoncom.CoUninitialize()

    def is_speaking(self):
        """Returns True if the TTS engine is currently speaking."""
        return self._is_speaking_flag.is_set()

    def say(self, text, interrupt=False):
        """
        Queues text to be spoken.
        Args:
            text (str): The text to be spoken.
            interrupt (bool): If True, clears any pending speech before this item
                              is queued, and the speech engine is told to purge.
        """
        # If interrupt is True, first clear the queue and send a silent stop to SAPI
        if interrupt:
            with self.queue.mutex:
                self.queue.queue.clear()
            self.queue.put((_ACTION_STOP_SILENT, None)) # This purges SAPI's buffer

        # Chunk the text into smaller pieces for better responsiveness
        if len(text) > _CHUNK_SIZE:
            # Using textwrap.wrap for robust word-aware splitting
            # SAPI also has its own chunking, but this makes our worker more responsive
            wrapped_chunks = textwrap.wrap(text, _CHUNK_SIZE, break_on_hyphens=False)
            
            # Ensure we don't send empty chunks
            chunks = [chunk.strip() for chunk in wrapped_chunks if chunk.strip()]

            # Enqueue each chunk as a separate speak command
            for chunk in chunks:
                self.queue.put((_ACTION_SPEAK, chunk))
        else:
            # For short texts, send as a single speak command
            self.queue.put((_ACTION_SPEAK, text))

    def stop(self):
        """
        Stops the current utterance and clears the speech queue.
        """
        with self.queue.mutex:
            self.queue.queue.clear()
        self.queue.put((_ACTION_STOP_SILENT, None))

    def set_rate(self, wpm_rate):
        """Sets the speaking rate in words-per-minute (approx)."""
        self.rate = wpm_rate
        rate_xml = f'<rate absspeed="{self._wpm_to_sapi_rate(self.rate)}"/>'
        self.queue.put((_ACTION_SET_RATE, rate_xml))

    def shutdown(self):
        """Stops the worker thread gracefully."""
        self.stop() # Stop any ongoing speech and clear queue
        self.queue.put((_ACTION_SHUTDOWN, None)) # Send shutdown signal
        self.thread.join() # Wait for thread to finish
