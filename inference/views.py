# inference/views.py
import os
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import default_storage

from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .services.ml_infer import predict_from_video
from .pipeline.Trimming_Video_Audio_Extraction import trim_video_to_speech

# If you created the model to log results:
try:
    from .models import InferenceResult
    HAVE_LOG_MODEL = True
except Exception:
    HAVE_LOG_MODEL = False

RUNTIME = Path(settings.INFER_RUNTIME_DIR)
RUNTIME.mkdir(parents=True, exist_ok=True)

def _save_uploaded_temp(dj_file) -> Path:
    """Save incoming file to local runtime dir for inference and return its path."""
    ext = os.path.splitext(dj_file.name)[1].lower() or ".mp4"
    temp_name = f"{uuid4().hex}{ext}"
    temp_path = RUNTIME / temp_name
    with open(temp_path, "wb") as out:
        for chunk in dj_file.chunks():
            out.write(chunk)
    return temp_path

def _storage_save_local_path(local_path: Path, key_prefix: str = "inference/") -> str:
    """
    Upload a local file to the configured DEFAULT_FILE_STORAGE (S3 via django-storages).
    Returns a public URL (S3 or configured storage).
    """
    key = f"{key_prefix}{local_path.name}"
    with open(local_path, "rb") as f:
        saved_path = default_storage.save(key, File(f))
    # Use storage's URL if available; else construct from MEDIA_URL
    try:
        return default_storage.url(saved_path)
    except Exception:
        return (settings.MEDIA_URL.rstrip("/") + "/" + saved_path.lstrip("/"))

class PredictView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (IsAuthenticated,)  # You can relax this for testing

    def post(self, request):
        """
        multipart/form-data with `video` field.
        Optional form fields:
          - save_outputs: "1" to upload trimmed video to S3 (default: 1)
          - log_db: "1" to store result row in DB if model exists (default: 1)
        """
        video = request.FILES.get("video")
        if not video:
            return Response({"detail": "No file field 'video'."}, status=status.HTTP_400_BAD_REQUEST)

        save_outputs = request.data.get("save_outputs", "1") in ("1", "true", "True")
        log_db = request.data.get("log_db", "1") in ("1", "true", "True")

        # 1) save to temp local path
        in_local = _save_uploaded_temp(video)

        # 2) run inference (this trims internally and writes features in runtime)
        try:
            result = predict_from_video(str(in_local))
        except Exception as e:
            return Response({"detail": f"Inference failed: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 3) figure out the trimmed file that the pipeline created (<stem>_speech.mp4)
        trimmed_local = RUNTIME / f"{in_local.stem}_speech.mp4"
        trimmed_url = ""
        in_url = ""

        # 4) Upload to S3 if requested
        if save_outputs:
            try:
                in_url = _storage_save_local_path(in_local)
            except Exception as e:
                in_url = ""
            if trimmed_local.exists():
                try:
                    trimmed_url = _storage_save_local_path(trimmed_local)
                except Exception:
                    trimmed_url = ""

        # 5) (optional) log to DB
        if HAVE_LOG_MODEL and log_db:
            try:
                row = InferenceResult.objects.create(
                    uploaded_by=request.user if request.user and request.user.is_authenticated else None,
                    input_video_url=in_url,
                    trimmed_video_url=trimmed_url,
                    top_class=result["top_class"],
                    probs=result["probs"],
                )
            except Exception:
                # don’t fail the request if DB logging fails
                row = None
        else:
            row = None

        # 6) response
        payload = {
            "top_class": result["top_class"],
            "probs": result["probs"],
            "input_video_url": in_url,
            "trimmed_video_url": trimmed_url,
            "logged_id": getattr(row, "id", None),
        }
        return Response(payload, status=status.HTTP_200_OK)
