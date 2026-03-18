import os
import logging
import redis
from flask import Flask, request
from cryptography.fernet import Fernet

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

def configure_redis():
    try:
        redis_client = redis.Redis(
            host=os.environ.get("REDIS_HOST"),
            port=os.environ.get("REDIS_PORT", 6379),
            db=0,
            password=os.environ.get("REDIS_PASSWORD")
        )
        return redis_client
    except redis.ConnectionError as e:
        logging.error(f"Redis connection error: {e}")
        exit(1)

def generate_secret_key():
    try:
        secret_key = Fernet.generate_key()
        return secret_key
    except Exception as e:
        logging.error(f"Failed to generate secret key: {e}")
        exit(1)

def set_redis_config(redis_client):
    try:
        config = {
            "secret_key": generate_secret_key(),
            "redis_client": redis_client
        }
        redis_client.set("config", config)
    except Exception as e:
        logging.error(f"Failed to set Redis config: {e}")
        exit(1)

def get_redis_config(redis_client):
    try:
        config = redis_client.get("config")
        return config
    except Exception as e:
        logging.error(f"Failed to get Redis config: {e}")
        exit(1)

def update_redis_config(redis_client):
    try:
        config = get_redis_config(redis_client)
        if config is not None:
            config = config.decode("utf-8")
            config = eval(config)
            secret_key = config["secret_key"]
            if secret_key != Fernet(secret_key).decrypt(b"test"):
                config["secret_key"] = Fernet.generate_key()
                set_redis_config(redis_client)
        else:
            config = {}
            set_redis_config(redis_client)
    except Exception as e:
        logging.error(f"Failed to update Redis config: {e}")
        exit(1)

if __name__ == "__main__":
    redis_client = configure_redis()
    update_redis_config(redis_client)
    app.run()