# Slack Flask Bot

This project is a Slack bot built using Flask. It listens for events and interactions from Slack and responds accordingly.

## Project Structure

```
slack-flask-bot
├── src
│   ├── bot.py
│   ├── config.py
│   ├── routes
│   │   └── slack_routes.py
│   └── utils
│       └── helpers.py
├── requirements.txt
└── README.md
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd slack-flask-bot
   ```

2. **Create a virtual environment:**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required packages:**
   ```
   pip install -r requirements.txt
   ```

4. **Configure your Slack app:**
   - Create a Slack app at [Slack API](https://api.slack.com/apps).
   - Add your Slack API tokens and other necessary configurations in `src/config.py`.

5. **Run the bot:**
   ```
   python src/bot.py
   ```

## Usage

- The bot will listen for events from Slack and respond based on the defined routes in `src/routes/slack_routes.py`.
- Utility functions in `src/utils/helpers.py` can be used to assist with message formatting and data processing.

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes.