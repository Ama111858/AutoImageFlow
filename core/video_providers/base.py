from abc import ABC, abstractmethod

class BaseVideoProvider(ABC):
    def __init__(self, config, download_folder):
        self.config = config
        self.download_folder = download_folder

    @abstractmethod
    def startup(self, progress_callback=None):
        pass

    @abstractmethod
    def generate_and_download(self, prompt, auto_name, auto_download, progress_callback, **kwargs):
        pass

    @abstractmethod
    def shutdown(self):
        pass
