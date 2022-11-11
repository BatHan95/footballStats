import json
import main
import logic.parsers as parser

API_KEY = json.loads(open('config.json', 'r').read())["API_KEY"]


def run(event, context):

    status = False
    updateText = ''

    try:
        if(event['api_key'] != API_KEY):
            response = {
                "statusCode": 200 if status else 403,
                "context": 'Issue with authentication'
            }

            return response
    except:
            response = {
                "statusCode": 200 if status else 403,
                "context": 'Issue with authentication'
            }

            return response

    if (event['action'] == 'refresh'):
        # Run refresh logic
        main.refresh()
        status = True
    elif (event['action'] == 'getBetsForTomorrow'):
        # Run get bets logic
        updateText = main.getBetsForTomorrow()
        status = True
    elif (event['action'] == 'getBetsForTomorrow_email'):
        response_raw = main.getBetsForTomorrow()
        response = parser.parse_bets_for_email(response_raw)
        return response
    else:
        raise Exception('No action provided')

    response = {
        "statusCode": 200 if status else 403,
        "context": updateText
    }

    return response

run({
  "api_key": "HhwhnMfuqhWnKQ@@b@7QI!T12H5JPqA4oKZrOy^B8UtVC$HbnejIPgj5jIvKJP3KAqS4oxe$^ULdxRlE2xzBuyHY9KhRc%2MSVJ",
  "action": "getBetsForTomorrow_email"
},{})