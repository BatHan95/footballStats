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
                response = {
                    "statusCode": 403,
                    "context": parser.parse_error('Issue with authentication - 403')
                }
                return response
        except:
                response = {
                    "statusCode": 403,
                    "context": parser.parse_error('Issue with authentication - 403')
                }
                return response
        
        try:
            event['action']
        except:
            updateText = parser.parse_error('No action provided')
            status = 400
            raise Exception('No action provided - 400')

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
            response_raw = main.getBetsForTomorrow()
            updateText = response_raw[0]
            response = parser.parse_bets_for_email(response_raw[0])
            updateText = response
            status = 200 if response_raw[1] else 500

        else:
            status = 400
            updateText = parser.parse_error(event['action'], 'is not a valid action')

    except:        
        response = {
            "statusCode": status,
            "context": updateText
        }
    
    response = {
            "statusCode": status,
            "context": updateText
    }

    return response

# print(run({
#     'api_key': API_KEY,
#     'action': 'refresh'
# },{}))