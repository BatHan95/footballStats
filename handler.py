import json
import main
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
        main.getBetsForTomorrow()
        status = True
    else:
        raise Exception('No action provided')

    response = {
        "statusCode": 200 if status else 403,
        "context": updateText
    }

    return response
