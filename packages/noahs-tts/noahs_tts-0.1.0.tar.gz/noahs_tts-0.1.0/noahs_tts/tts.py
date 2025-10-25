
import pyttsx3
import re

class TTS:
    def __init__(self, voice: str | None = None, rate: float | None = None):
        self.engine = pyttsx3.init()
        if voice:
            self._set_voice(voice)
        if rate:
            self.engine.setProperty('rate', int(rate))

    def voices(self):
        out = []
        for v in self.engine.getProperty('voices'):
            out.append({
                "id": v.id,
                "name": getattr(v, "name", v.id),
                "locale": getattr(v, "languages", [None])[0],
                "gender": getattr(v, "gender", None),
            })
        return out

    def _set_voice(self, voice_id_or_name: str):
        for v in self.engine.getProperty('voices'):
            if voice_id_or_name.lower() in (v.id.lower(), getattr(v, "name", "").lower()):
                self.engine.setProperty('voice', v.id)
                return

    def say(self, text: str, split_sentences:bool=True):
        def _split_sentences(t: str):
            return re.split(r'(?<=[.!?])\s+', t.strip())
        if split_sentences:
            for chunk in _split_sentences(text):
                self.engine.say(chunk)
        else:
            self.engine.say(text)
        self.engine.runAndWait()

    def synth(self, text: str, voice: str | None = None, rate: float | None = None) -> bytes:
        if voice:
            self._set_voice(voice)
        if rate:
            self.engine.setProperty('rate', int(rate))
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            temp_path = tmp.name
        try:
            self.engine.save_to_file(text, temp_path)
            self.engine.runAndWait()
            with open(temp_path, "rb") as f:
                data = f.read()
            return data
        finally:
            try: os.remove(temp_path)
            except OSError: pass

    def save(self, text: str, path: str, **opts):
        data = self.synth(text, **opts)
        with open(path, "wb") as f:
            f.write(data)










if __name__ == "__main__":
    tts = TTS()
    tts.say("hello")













