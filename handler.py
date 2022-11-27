import json
import main
import logic.parsers as parser

API_KEY = json.loads(open('config.json', 'r').read())["API_KEY"]

def run(event, context):

    status = False
    updateText = ''
    try:

        ### Poorly Handelled Checks
        try:
            if(event['api_key'] != API_KEY):
                raise Exception('Wrong API Key')
        except:
                response = {
                    "statusCode": 403,
                    "context": parser.parse_error('Issue with authentication ')
                }
                return response
        
        try:
            event['action']
        except:
            response = {
                "statusCode": 400,
                "context": parser.parse_error('No action provided')
            }
            return response

        ### Events

        if (event['action'] == 'refresh'):
            # Run refresh logic
            refresh = main.refresh()
            updateText = f'Refresh - { refresh[0] }'
            status = 200 if refresh[1] else 500

        elif (event['action'] == 'getBetsForTomorrow'):
            # Run get bets logic
            betsTomorrow = main.getBetsForTomorrow()
            updateText = betsTomorrow[0]
            status = 200 if betsTomorrow[1] else 500

        elif (event['action'] == 'getBetsForTomorrow_email'):
            # Run get bets logic and parse for email
            response_raw = main.getBetsForTomorrow()
            updateText = response_raw[0]
            response = parser.parse_bets_for_email(response_raw[0])
            updateText = response
            status = 200 if response_raw[1] else 500

        else:
            status = 400
            updateText = parser.parse_error(event['action'], 'is not a valid action')

    except Exception as e:
        status = 500
        print(e)
        updateText = 'Some issue somewhere, we didnt know about it before now thou'
    
    response = {
            "statusCode": status,
            "context": updateText
    }

    return response

# print(run({
#     'api_key': "API_KEY",
#     'action': 'refresh'
# },{}))