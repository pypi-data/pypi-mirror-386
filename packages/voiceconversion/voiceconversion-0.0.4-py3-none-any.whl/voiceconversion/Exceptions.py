class VoiceChangerIsNotSelectedException(Exception):
    def __str__(self):
        return repr("Voice Changer is not selected.")


class PretrainDownloadException(Exception):
    def __str__(self):
        return repr("Failed to download pretrain models.")

class DownloadVerificationException(Exception):
    def __init__(self, filename: str, got_hash: str, expected_hash: str) -> None:
        self.filename = filename
        self.got_hash = got_hash
        self.expected_hash = expected_hash

    def __str__(self):
        return repr(f"{self.filename} failed to pass hash verification check. Got {self.got_hash}, expected {self.expected_hash}")

class PipelineCreateException(Exception):
    def __str__(self):
        return repr("Failed to create Pipeline.")


class PipelineNotInitializedException(Exception):
    def __str__(self):
        return repr("Pipeline is not initialized.")
