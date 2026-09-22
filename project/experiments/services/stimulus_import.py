"""Parses a researcher's ZIP upload (images + vocab .txt files) into a
StimulusSet: validates it, uploads images to storage, and builds the
`vocab_data` JSON (BRD 2.2-2.6)."""
import os
import re
import zipfile

import structlog
from django.core.files.base import ContentFile

from moses.common.exceptions import CustomAPIException, KwargsError

from project import errors
from project.experiments.models import StimulusSet

logger = structlog.get_logger(__name__)

_IMAGE_EXTENSIONS = {'.jpg', '.jpeg'}
# One line: "<stem><tab-or-whitespace><answers separated by ; or ,>"
_LINE_RE = re.compile(r'^(?P<stem>\S+)[ \t]+(?P<answers>.+)$')


def parse_vocab_text(text: str) -> dict[str, list[str]]:
    """{"beetle": ["жук", "букашка"], ...} — raises on an unparseable line."""
    parsed = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = _LINE_RE.match(line)
        if not match:
            raise CustomAPIException({
                '': [KwargsError(kwargs={'line': line}, code=errors.INVALID_VOCAB_FORMAT)]
            })
        answers = [a.strip() for a in re.split(r'[;,]', match['answers']) if a.strip()]
        if not answers:
            raise CustomAPIException({
                '': [KwargsError(kwargs={'line': line}, code=errors.INVALID_VOCAB_FORMAT)]
            })
        parsed[match['stem'].strip()] = answers
    return parsed


def import_stimulus_archive(zip_file, user, name: str = '') -> StimulusSet:
    if zip_file.size > _max_archive_bytes():
        raise CustomAPIException({'archive': [KwargsError(code=errors.ARCHIVE_TOO_LARGE)]})

    try:
        archive = zipfile.ZipFile(zip_file)
    except zipfile.BadZipFile:
        raise CustomAPIException({'archive': [KwargsError(code=errors.INVALID_ARCHIVE)]})

    entries = [n for n in archive.namelist() if not n.endswith('/') and '__MACOSX' not in n]
    if not entries:
        raise CustomAPIException({'archive': [KwargsError(code=errors.INVALID_ARCHIVE)]})

    image_names = [n for n in entries if os.path.splitext(n)[1].lower() in _IMAGE_EXTENSIONS]
    vocab_names = [n for n in entries if n.lower().endswith('.txt')]
    if not image_names:
        raise CustomAPIException({'archive': [KwargsError(code=errors.NO_IMAGES_IN_ARCHIVE)]})
    if not vocab_names:
        raise CustomAPIException({'archive': [KwargsError(code=errors.NO_VOCAB_IN_ARCHIVE)]})

    for n in image_names:
        if archive.getinfo(n).file_size > _max_image_bytes():
            raise CustomAPIException({
                'archive': [KwargsError(kwargs={'file': n}, code=errors.ARCHIVE_TOO_LARGE)]
            })

    basenames = {os.path.basename(n): n for n in image_names}
    stem_to_basename = {os.path.splitext(b)[0].lower(): b for b in basenames}

    vocab_data = {}
    for vn in vocab_names:
        parsed = parse_vocab_text(archive.read(vn).decode('utf-8'))
        for stem, answers in parsed.items():
            basename = stem_to_basename.get(stem.lower())
            if basename is None:
                logger.warning("vocab_entry_without_image", stem=stem, vocab_file=vn)
                continue
            vocab_data[basename] = answers

    stimulus_set = StimulusSet(
        user=user, name=name, stimulus_count=len(basenames), vocab_data=vocab_data,
    )
    from project.storages import PublicMediaStorage

    stimulus_set.s3_path = f'stimulus_sets/{stimulus_set.id}/'
    storage = PublicMediaStorage()
    for basename, member_name in basenames.items():
        storage.save(f'{stimulus_set.s3_path}{basename}', ContentFile(archive.read(member_name)))
    stimulus_set.save()
    logger.info(
        "stimulus_set_imported", stimulus_set_id=str(stimulus_set.id),
        stimulus_count=stimulus_set.stimulus_count, matched_vocab=len(vocab_data),
    )
    return stimulus_set


def _max_archive_bytes() -> int:
    from django.conf import settings
    return settings.STIMULUS_ARCHIVE_MAX_BYTES


def _max_image_bytes() -> int:
    from django.conf import settings
    return settings.STIMULUS_IMAGE_MAX_BYTES
