from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os

class MediaStorage(FileSystemStorage):
    def __init__(self, location=None, base_url=None):
        if location is None:
            location = os.path.join(settings.BASE_DIR, 'media')
        if base_url is None:
            base_url = '/media/'
        super().__init__(location, base_url)

    def get_available_name(self, name, max_length=None):
        # Don't overwrite existing files
        if self.exists(name):
            name = self.get_available_name(name)
        return name