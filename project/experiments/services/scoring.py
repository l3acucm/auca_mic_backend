"""Trial outcome codes (BRD 4.1). Codes shared with the frontend and the
XLSX export. `code_response` (text-vs-vocab matching) was removed along
with the recognized-text transcript — see BRD changelog: Chrome's cloud
speech backend produced no usable transcript in practice, so `CORRECT` now
just means "a voice was detected" (`onspeechstart`), not "said the right
word"."""

CORRECT = 1
INCORRECT = 0
SKIPPED = 2
ERROR = 3
