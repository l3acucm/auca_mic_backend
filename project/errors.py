# App-wide error code constants. Returned as
# {"errors": {"<field>": [{"error_code": "...", "kwargs": {...}}]}, "data": {}}
# by moses' CustomAPIException + custom_exception_handler.

INVALID_ARCHIVE = 'invalid_archive'
ARCHIVE_TOO_LARGE = 'archive_too_large'
NO_IMAGES_IN_ARCHIVE = 'no_images_in_archive'
NO_VOCAB_IN_ARCHIVE = 'no_vocab_in_archive'
INVALID_VOCAB_FORMAT = 'invalid_vocab_format'
EXPERIMENT_ARCHIVED = 'experiment_archived'
SESSION_ALREADY_COMPLETED = 'session_already_completed'
SESSION_NOT_FOUND = 'session_not_found'
UNKNOWN_STIMULUS = 'unknown_stimulus'
