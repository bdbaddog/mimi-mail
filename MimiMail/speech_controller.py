"""
SpeechController - Thread-safe TTS controller using command queue pattern.

Single thread owns the pyttsx3 engine and processes all speech commands.
UI communicates via thread-safe methods, no shared mutable state.
"""

import pyttsx3
import threading
import queue


class SpeechController:
    def __init__(self, rate=130):
        self._command_queue = queue.Queue()
        self._rate = rate

        # State owned exclusively by worker thread
        self._speaking = False
        self._resumable_words = []
        self._resumable_index = 0

        # Thread-safe state for UI to query
        self._speaking_lock = threading.Lock()
        self._is_speaking = False

        # Start worker thread
        self._running = True
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def _worker_loop(self):
        """Main loop - processes commands and owns the TTS engine."""
        engine = pyttsx3.init()
        engine.setProperty('rate', self._rate)

        while self._running:
            try:
                # Wait for command with timeout to allow checking _running
                cmd = self._command_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if cmd[0] == 'SPEAK':
                _, text, resumable = cmd
                self._do_speak(engine, text, resumable)
            elif cmd[0] == 'STOP':
                self._do_stop(engine)
            elif cmd[0] == 'SET_RATE':
                _, rate = cmd
                self._rate = rate
                engine.setProperty('rate', rate)
            elif cmd[0] == 'SHUTDOWN':
                self._running = False
                break

            self._command_queue.task_done()

        # Cleanup
        try:
            engine.stop()
        except:
            pass

    def _do_speak(self, engine, text, resumable):
        """Execute speak command."""
        with self._speaking_lock:
            self._is_speaking = True

        if resumable:
            self._speak_resumable(engine, text)
        else:
            self._speak_simple(engine, text)

        with self._speaking_lock:
            self._is_speaking = False

    def _speak_simple(self, engine, text):
        """Speak entire text without tracking position."""
        # Clear any resumable state
        self._resumable_words = []
        self._resumable_index = 0

        engine.say(text)
        engine.runAndWait()

    def _speak_resumable(self, engine, text):
        """Speak text with pause/resume support."""
        words = text.split()

        # Check if resuming same text
        if words == self._resumable_words and self._resumable_index > 0:
            start_index = self._resumable_index
        else:
            self._resumable_words = words
            self._resumable_index = 0
            start_index = 0

        chunk_size = 20
        current_index = start_index

        while current_index < len(self._resumable_words):
            # Check for stop command (non-blocking)
            try:
                cmd = self._command_queue.get_nowait()
                if cmd[0] == 'STOP':
                    self._resumable_index = current_index
                    self._command_queue.task_done()
                    return
                elif cmd[0] == 'SET_RATE':
                    _, rate = cmd
                    self._rate = rate
                    engine.setProperty('rate', rate)
                    self._command_queue.task_done()
                # Ignore other commands while speaking
            except queue.Empty:
                pass

            end_index = min(current_index + chunk_size, len(self._resumable_words))
            chunk = ' '.join(self._resumable_words[current_index:end_index])

            engine.say(chunk)
            engine.runAndWait()

            current_index = end_index
            self._resumable_index = current_index

        # Finished completely - reset
        self._resumable_words = []
        self._resumable_index = 0

    def _do_stop(self, engine):
        """Execute stop command."""
        try:
            engine.stop()
        except:
            pass

        with self._speaking_lock:
            self._is_speaking = False

    # Public API - thread-safe methods for UI

    def speak(self, text, resumable=False):
        """Start speaking text. If resumable=True, supports pause/resume."""
        self._command_queue.put(('SPEAK', text, resumable))

    def stop(self):
        """Stop current speech."""
        # Clear any pending commands first
        try:
            while True:
                self._command_queue.get_nowait()
                self._command_queue.task_done()
        except queue.Empty:
            pass

        self._command_queue.put(('STOP',))

        with self._speaking_lock:
            self._is_speaking = False

    def set_rate(self, rate):
        """Set speech rate."""
        self._command_queue.put(('SET_RATE', rate))

    def is_speaking(self):
        """Check if currently speaking (thread-safe)."""
        with self._speaking_lock:
            return self._is_speaking

    def shutdown(self):
        """Shutdown the controller."""
        self.stop()
        self._command_queue.put(('SHUTDOWN',))
        self._worker.join(timeout=2.0)

    def reset_resumable(self):
        """Reset resumable state (call when entering new message)."""
        # Send a marker that the worker will process
        self._resumable_words = []
        self._resumable_index = 0
