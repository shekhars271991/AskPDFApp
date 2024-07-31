import os
from app import create_app

config_class = os.getenv('FLASK_CONFIG', 'config.DevConfig')
print(f"Loading configuration: {config_class}")

app = create_app(config_class=config_class)

if __name__ == '__main__':
    app.run()
