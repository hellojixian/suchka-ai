from mongoengine import connect
from dotenv import load_dotenv
import os

class Database:
  def __init__(self):
    load_dotenv()
    if os.getenv("MONGODB_URI") is None:
      self.uri = "mongodb://localhost:27017/suchka-ai"
    self.uri = os.getenv("MONGODB_URI")
    self.conn = connect(host=self.uri)

  def get_connection(self):
    return self.conn