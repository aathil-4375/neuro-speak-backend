# inference/models.py
from django.db import models
from django.conf import settings

class InferenceResult(models.Model):
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="inference_results"
    )
    input_video_url = models.URLField(max_length=1024, blank=True)
    trimmed_video_url = models.URLField(max_length=1024, blank=True)
    top_class = models.CharField(max_length=255)
    probs = models.JSONField()  # [{'label': 'x', 'p': 0.12}, ...]
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.top_class} @ {self.created_at:%Y-%m-%d %H:%M}"
