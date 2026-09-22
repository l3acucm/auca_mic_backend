"""Add one stimulus (image + accepted answers) to a StimulusSet at a time —
the researcher UI builds a set up incrementally instead of uploading a
pre-packaged ZIP (BRD 2.2, redesigned)."""
import os
import re

import structlog
from django.conf import settings
from django.core.files.base import ContentFile

from moses.common.exceptions import CustomAPIException, KwargsError

from project import errors
from project.experiments.models import StimulusSet

logger = structlog.get_logger(__name__)

_IMAGE_EXTENSIONS = {'.jpg', '.jpeg'}


def parse_answers(text: str) -> list[str]:
    return [a.strip() for a in re.split(r'[;,]', text or '') if a.strip()]


def add_stimulus(stimulus_set: StimulusSet, image, answers_text: str) -> None:
    filename = os.path.basename(image.name)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in _IMAGE_EXTENSIONS:
        raise CustomAPIException({
            'image': [KwargsError(kwargs={'filename': filename}, code=errors.INVALID_IMAGE_EXTENSION)]
        })
    if image.size > settings.STIMULUS_IMAGE_MAX_BYTES:
        raise CustomAPIException({'image': [KwargsError(code=errors.IMAGE_TOO_LARGE)]})
    if filename in stimulus_set.vocab_data:
        raise CustomAPIException({
            'image': [KwargsError(kwargs={'filename': filename}, code=errors.STIMULUS_ALREADY_EXISTS)]
        })

    answers = parse_answers(answers_text)
    if not answers:
        raise CustomAPIException({'answers': [KwargsError(code=errors.EMPTY_ANSWERS)]})

    from project.storages import PublicMediaStorage
    PublicMediaStorage().save(f'{stimulus_set.s3_path}{filename}', ContentFile(image.read()))

    stimulus_set.vocab_data[filename] = answers
    stimulus_set.save(update_fields=['vocab_data'])
    logger.info(
        "stimulus_added", stimulus_set_id=str(stimulus_set.id), filename=filename, answers=answers
    )
