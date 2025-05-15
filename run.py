from flask import Flask
from Routes.Slack_routes import bp as slack_bp

app = Flask(__name__)
app.register_blueprint(slack_bp)

if __name__ == "__main__":
    app.run(port=3000, debug=True)
