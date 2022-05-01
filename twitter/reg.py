import tweepy, os, dotenv

dotenv.load_dotenv()


CONSUMER_KEY = os.getenv('tapikey')
CONSUMER_SECRET = os.getenv('tapisecret')

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.secure = True
auth_url = auth.get_authorization_url()

print("Please authorize:", auth_url)

verifier = input('PIN: ').strip()

auth.get_access_token(verifier)

print(auth.__dict__)

print()

print("ACCESS_KEY =", auth.access_token)
print("ACCESS_SECRET =", auth.access_token_secret)