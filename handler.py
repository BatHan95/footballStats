import json
import main
API_KEY = json.loads(open('config.json', 'r').read())["API_KEY"]

def run(event, context):

    status = False
    updateText = ''
    try:
        if(event['api_key'] == API_KEY):
            try:
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
            except:
                updateText = 'Issue with the action'
        else:
            raise Exception('Incorrect API Key')
    except:
        updateText = 'Issue with authentication'

    response = {
        "statusCode": 200 if status else 403,
        "context": updateText
    }

    return response
