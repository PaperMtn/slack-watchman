### SLACK SEARCH QUERIES ###
# List of queries to find private keys
PRIVATE_KEYS = ["BEGIN DSA PRIVATE",
                "BEGIN EC PRIVATE",
                "BEGIN OPENSSH PRIVATE",
                "BEGIN PGP PRIVATE",
                "BEGIN RSA PRIVATE"]

# List of queries to find passwords
PASSWORD_QUERIES = ['"password:"*',
                    '"password is"*',
                    'pwd',
                    'passwd']

# List of queries to find bank cards
BANK_CARD_QUERIES = ['cvv',
                     'card',
                     'cardno',
                     '"card no:"',
                     '"card number:"',
                     '4026*',
                     '417500*',
                     '4508*',
                     '4844*',
                     '4913*',
                     '4917*']

# List of queries to find files
FILE_EXTENSIONS = ['.exe',
                   '.zip',
                   '.doc',
                   '.docx',
                   '.docm',
                   '.xls',
                   '.xlsx',
                   '.xlsm',
                   '.conf']

# List of queries to find certificate files
CERTIFICATE_EXTENSIONS = ['.key',
                          '.p12',
                          '.pem',
                          '.pfx',
                          '.pkcs12']

# List of queries to find GCP credential files
GCP_CREDENTIAL_EXTENSIONS = ['.json']

# List of queries to find AWS keys
AWS_KEYS_QUERIES = ['ASIA*',
                    'AKIA*']

# List of queries to find Slack API keys
SLACK_KEY_QUERIES = ['xoxb*',
                     'xoxa*',
                     'xoxp*',
                     'xoxr*',
                     'xoxs*']

### REGEX ###
# Regex to detect private keys - Credit: emtunc - SlackPirate
PRIVATE_KEYS_REGEX = r"([-]+BEGIN [^\s]+ PRIVATE KEY[-]+[\s]*[^-]*[-]+END [^\s]+ PRIVATE KEY[-]+)"

# Regex to detect passwords - Credit: emtunc - SlackPirate
PASSWORD_REGEX = r"(?i)(password\s*[`=:\"]+\s*[^\s]+|password is\s*[`=:\"]*\s*[^\s]+|pwd\s*[`=:\"]*\s*[" \
                 r"^\s]+|passwd\s*[`=:\"]+\s*[^\s]+) "

# Regex to detect bank cards
BANK_CARD_REGEX = r"^(?:5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|27[01][0-9]|2720)[0-9]{12}$|^4[0-9]{12}(" \
                  r"?:[0-9]{3})?$|^3[47][0-9]{13}$|^6(?:011|5[0-9]{2})[0-9]{12}$|^(?:2131|1800|35\d{3})\d{11}$ "

# Regex to detect AWS keys
AWS_KEYS_REGEX = r"(?!com/archives/[A-Z0-9]{9}/p[0-9]{16})((?<![A-Za-z0-9/+])[A-Za-z0-9/+]{40}(?![A-Za-z0-9/+])|(?<![" \
                 r"A-Z0-9])[A-Z0-9]{20}(?![A-Z0-9])) "

# Regex to detect Slack API keys
SLACK_REGEX = r"xox[baprs]([0-9a-zA-Z-]{10,72})"

### TIMEFRAMES ###
# Epoch time for 30 days
MONTH_TIMEFRAME = 2592000

# Epoch time for 7 days
WEEK_TIMEFRAME = 604800

# Epoch time for... a very long time
# If you have Slack messages going back 50 years, bravo time traveller
ALL_TIME = 1576800000
