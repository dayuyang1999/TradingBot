from simplegmail import Gmail








if __name__ == '__main__':
    gmail = Gmail() # will open a browser window to ask you to log in and authenticate

    params = {
    "to": "dayu@udel.com",
    "sender": "yangdayu1997@gmail.com",
    "subject": 'Stock Bot Stop working! Need attention immediately!',
    "msg_html": "<h1>check https://app.alpaca.markets/paper/dashboard/overview</h1><br /> Blank for later usage.",
    "msg_plain": "Hi\nThis is a plain text email.",
    "signature": True  # use my account signature
    }
    message = gmail.send_message(**params) 