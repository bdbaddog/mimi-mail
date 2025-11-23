import sys
import queue
import threading
import pythoncom
import win32com.client

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
        self.thread.start()

    def _wpm_to_sapi_rate(self, wpm):
        """Converts words-per-minute (approx) to SAPI's -10 to 10 scale."""
        # This is a rough linear conversion.
        # Default pyttsx3 rate is 200, default SAPI seems to be around 150-180 WPM.
        # Let's map 150 WPM to SAPI rate 0.
        return max(-10, min(10, int((wpm - 150) / 10)))

    def _worker(self):
        """The single worker thread that owns the SAPI voice object."""
        pythoncom.CoInitialize()
        try:
            voice = win32com.client.Dispatch("SAPI.SpVoice")
            voice.Rate = self._wpm_to_sapi_rate(self.rate)
            while True:
                interrupt, text = self.queue.get()
                if text is None: # Shutdown signal
                    break

                # SVSFPurgeBeforeSpeak = 1, SVSFDefault/SVSFlagsAsync = 0
                # We use flags=1 to interrupt, which purges pending sounds.
                flags = 1 if interrupt else 0
                voice.Speak(text, flags)
                self.queue.task_done()
        finally:
            pythoncom.CoUninitialize()

    def say(self, text, interrupt=False):
        """
        Queues text to be spoken.
        Args:
            text (str): The text to be spoken.
            interrupt (bool): If True, stops the current speech before queuing.
        """
        # For SAPI, the interrupt is handled by the Speak flag.
        # If we want an immediate stop without saying something new, use stop().
        if interrupt:
            self.stop()
        
        self.queue.put((interrupt, text))

    def stop(self):
        """
        Clears the queue and stops the current utterance.
        """
        # Clear any pending items from our queue
        with self.queue.mutex:
            self.queue.queue.clear()
        
        # Send an empty string with the purge flag to interrupt current speech
        self.queue.put((True, ''))

    def set_rate(self, wpm_rate):
        """Sets the speaking rate in words-per-minute (approx)."""
        self.rate = wpm_rate
        # To change the rate of the existing object, we would need to pass
        # this command to the worker thread. This is a simple way:
        self.queue.put((False, f'<rate absspeed="{self._wpm_to_sapi_rate(self.rate)}"/>'))

    def shutdown(self):
        """Stops the worker thread gracefully."""
        self.stop() # Clear queue and stop current speech
        self.queue.put((False, None)) # Send shutdown signal
        self.thread.join() # Wait for thread to finish
