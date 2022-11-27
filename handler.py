import json
import main
import logic.parsers as parser

API_KEY = json.loads(open('config.json', 'r').read())["API_KEY"]

def run(event, context):

    status = False
    updateText = ''
    try:
        try:
            if(event['api_key'] != API_KEY):
                response = {
                    "statusCode": 200 if status else 400,
                    "context": '403 - Issue with authentication'
                }
                return response
        except:
                response = {
                    "statusCode": 200 if status else 400,
                    "context": '403 - Issue with authentication'
                }
                return response
        
        try:
            event['action']
        except:
            updateText = '400 - No action provided'
            raise Exception('No action provided')

        if (event['action'] == 'refresh'):
            # Run refresh logic
            main.refresh()
            updateText = '200 - Refresh Successful'
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
            updateText = f"""{event['action']} is not a valid action"""

    except:
        response = {
            "statusCode": 200 if status else 400,
            "context": updateText
        }
    
    response = {
            "statusCode": 200 if status else 400,
            "context": updateText
    }

    return json.dumps(response)

print(run({
    'api_key': API_KEY,
    'action': 'test_email'
},{}))