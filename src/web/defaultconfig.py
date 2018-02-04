
DEBUG = False
TESTING = False

REDIS_HOSTNAME             = "127.0.0.1"
REDIS_PORT                 = 6379
REDIS_GAMES_STORE          = "games"
REDIS_GAMES_REQ_QUEUE      = "reqs"
REDIS_GAMES_CNF_QUEUE      = "cnfs"

# Games will be deleted without result if no move (from either player) was made during this time.
GAME_MAX_LENGTH  = 3600

