# App-wide error code constants. Returned as
# {"errors": {"<field>": [{"error_code": "...", "kwargs": {...}}]}, "data": {}}
# by moses' CustomAPIException + custom_exception_handler.

INVALID_IMAGE_EXTENSION = 'invalid_image_extension'
IMAGE_TOO_LARGE = 'image_too_large'
EMPTY_ANSWERS = 'empty_answers'
STIMULUS_ALREADY_EXISTS = 'stimulus_already_exists'
EXPERIMENT_ARCHIVED = 'experiment_archived'
SESSION_ALREADY_COMPLETED = 'session_already_completed'
SESSION_NOT_FOUND = 'session_not_found'
UNKNOWN_STIMULUS = 'unknown_stimulus'
