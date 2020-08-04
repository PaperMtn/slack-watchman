### SLACK SEARCH QUERIES ###
# List of queries to find private keys
PRIVATE_KEYS_QUERIES = ['BEGIN DSA PRIVATE',
                'BEGIN EC PRIVATE',
                'BEGIN OPENSSH PRIVATE',
                'BEGIN PGP PRIVATE',
                'BEGIN RSA PRIVATE']

# List of queries to find passwords
PASSWORD_QUERIES = ['"password:"*',
                    '"password is"*',
                    'pwd',
                    'passwd']

# List of queries to find bank cards
BANK_CARD_QUERIES = ['cvv',
                     'mastercard',
                     'cardno',
                     'visa',
                     '"american express"',
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
                          '.pkcs12',
                          '.crt',
                          '.cert']

# List of queries to find GCP credential files
GCP_CREDENTIAL_EXTENSIONS = ['.json']

# List of queries to find GCP credentials
GCP_CREDENTIAL_QUERIES = ['"-----BEGIN PRIVATE KEY-----"']

# List of queries to find Google API keys
GOOGLE_API_QUERIES = ['AIza',
                      '.apps.googleusercontent.com']

# List of queries to find AWS keys
AWS_KEYS_QUERIES = ['ASIA*',
                    'AKIA*']

# List of queries to find Slack API keys
SLACK_KEY_QUERIES = ['xoxb*',
                     'xoxa*',
                     'xoxp*',
                     'xoxr*',
                     'xoxs*']

# List of queries to find Slack webhooks
SLACK_WEBHOOK_QUERIES = ['https://hooks.slack.com/']

# List of queries to find PayPal Braintree access tokens
PAYPAL_QUERIES = ['paypal',
                  'braintree']

# List of queries to find dates of birth
DOB_QUERIES = ['date of birth',
               'dob',
               'birthday']

# List of queries to find passport numbers
PASSPORT_QUERIES = ['PassportID',
                    'passport',
                    'Passportno',
                    'passportnumber']

# List of queries to find Twitter API keys
TWITTER_QUERIES = ['api.twitter.com',
                   'twitter api',
                   '"oauth_token"_secret']

# List of queries to find Facebook tokens
FACEBOOK_QUERIES = ['graph.facebook.com',
                    'facebook.com/dialog/oauth',
                    'eaaced',
                    'client_secret']

GITHUB_QUERIES = ['api.github.com',
                  'github.com/login/oauth/',
                  'github access_token']

IBAN_QUERIES = ['iban']

SSN_US_QUERIES = ['ssn',
                  'social security']

NI_NUMBER_QUERIES = ['national insurance',
                     'ni number']

CUSIP_QUERIES = ['cusip']

DRIVERS_LICENCE_UK_QUERIES = ['drivers licence']

ITIN_QUERIES = ['itin',
                'tin',
                'Individual Taxpayer Identification Number']

BEARER_TOKEN_QUERIES = ["'Authorization': 'Bearer"]

### REGEX ###
# Regex to detect private keys - Credit: emtunc - SlackPirate
PRIVATE_KEYS_REGEX = r"([-]+BEGIN [^\s]+ PRIVATE KEY[-]+[\s]*[^-]*[-]+END [^\s]+ PRIVATE KEY[-]+)"

# Regex to detect passwords - Credit: emtunc - SlackPirate
PASSWORD_REGEX = r"(?i)(password\s*[`=:\"]+\s*[^\s]+|password is\s*[`=:\"]*\s*[^\s]+|pwd\s*[`=:\"]*\s*[" \
                 r"^\s]+|passwd\s*[`=:\"]+\s*[^\s]+) "

# Regex to detect bank cards
BANK_CARD_REGEX = r"^((67\d{2})|(4\d{3})|(5[1-5]\d{2})|(6011))-?\s?\d{4}-?\s?\d{4}-?\s?\d{4}|3[4,7]\d{13}$"

# Regex to find Google API keys
GOOGLE_API_REGEX = r"AIza[0-9A-Za-z\\-_]{35}|[0-9]+-[0-9A-Za-z_]{32}.apps.googleusercontent.com"

# Regex to detect AWS keys
AWS_KEYS_REGEX = r"(?!com/archives/[A-Z0-9]{9}/p[0-9]{16})((?<![A-Za-z0-9/+])[A-Za-z0-9/+]{40}(?![A-Za-z0-9/+])|(?<![" \
                 r"A-Z0-9])[A-Z0-9]{20}(?![A-Z0-9]))"

# Regex to detect GCP credentials
GCP_CREDENTIAL_REGEX = r"([-]+BEGIN PRIVATE KEY[-]+[\s]*[^-]*[-]+END PRIVATE KEY[-]+)"

# Regex to detect Slack API keys
SLACK_API_REGEX = r"xox[baprs]([0-9a-zA-Z-]{10,72})"

# Regex to detect Slack webhooks
SLACK_WEBHOOK_REGEX = r"https://hooks.slack.com/services/T[a-zA-Z0-9_]{8}/B[a-zA-Z0-9_]{8}/[a-zA-Z0-9_]{24}"

# Regex to detect Braintree tokens
PAYPAL_REGEX = r"access_token\\$production\\$[0-9a-z]{16}\\$[0-9a-f]{32}"

# Regex to detect dates of birth
DOB_REGEX = r"(19|20)\d\d([- \/.])(0[1-9]|1[012])\2(0[1-9]|[12][0-9]|3[01])$|^([0-2][0-9]|(3)[0-1])([- \/.])(((0)[" \
            r"0-9])|((1)[0-2]))([- \/.])\d{2,4}$ "

# Regex to detect passport numbers
PASSPORT_REGEX = r"\b[a-zA-Z0-9]{2}[0-9]{5,10}\b"

# Regex to detect Twitter API keys
TWITTER_REGEX = r"api\.twitter\.com\/oauth.*[0-9a-zA-Z]{35,44}|api\.twitter\.com\/oauth.*[1-9][0-9]+-[0-9a-zA-Z]{40}|" \
                r"([t|T][w|W][i|I][t|T][t|T][e|E][r|R]|oauth_token).*[0-9a-zA-Z]{35,44}"

# Regex to detect Facebook access tokens
FACEBOOK_ACCESS_TOKEN_REGEX = r'EAACEdEose0cBA[0-9A-Za-z]+'

# Regex to detect Facebook secret keys
FACEBOOK_SECRET_REGEX = r'[f|F][a|A][c|C][e|E][b|B][o|O][o|O][k|K].*[0-9a-f]{32}'

# Regex to detect GitHub API keys
GITHUB_REGEX = r'[0-9a-zA-Z]{20,40}'

# Regex to detect IBAN numbers
IBAN_REGEX = r"([A-Za-z]{2}[ \-]?[0-9]{2})(?=(?:[ \-]?[A-Za-z0-9]){9,30}$)((?:[ \-]?[A-Za-z0-9]{3,5}){2,7})([ \-]?[" \
             r"A-Za-z0-9]{1,3})?$"

# Regex to detect US Social Security Numbers
SSN_US_REGEX = r'((?!000)(?!666)(?:[0-6]\d{2}|7[0-2][0-9]|73[0-3]|7[5-6][0-9]|77[0-2]))-((?!00)\d{2})-((?!0000)\d{4})'

# Regex to detect National Insurance Numbers
NI_NUMBER_REGEX = r'(?!BG|GB|NK|KN|TN|NT|ZZ)[A-Ca-cEeGgHhJ-Pj-pR-Tr-tW-Zw-z][A-Ca-cEeGgHhJ-Nj-nPpR-Tr-tW-Zw-z](' \
                  r'?:\s*\d{2}){3}\s*[A-Da-d]'

# Regex to detect CUSIP numbers
CUSIP_REGEX = r'\s[0-9]{3}[a-zA-Z0-9]{6}\s'

DRIVERS_LICENCE_UK_REGEX = r'[A-Za-z9]{5}\d{6}[A-Za-z9]{2}\d[A-Za-z]{2}'

ITIN_REGEX = r'9\d{2}-?((5[0-9]|6[0-5])|(8[3-8])|(9[0-2])|(9[4-9]))-?\d{4}'

BEARER_TOKEN_REGEX = r'''('|"){0,2}Bearer\s([0-9a-zA-Z!@#$&()\/\-`_.+,"]{30,})('|"){0,2}'''

### TIMEFRAMES ###
# Epoch time for 24 hours
DAY_TIMEFRAME = 86400

# Epoch time for 30 days
MONTH_TIMEFRAME = 2592000

# Epoch time for 7 days
WEEK_TIMEFRAME = 604800

# Epoch time for... a very long time
# If you have Slack messages going back 50 years, bravo time traveller
# If this project, Slack or indeed the planet is still here in 50 years, we'll have all done well.
ALL_TIME = 1576800000
