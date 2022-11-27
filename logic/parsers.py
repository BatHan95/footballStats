import html

def parse_bets_for_email(data):

    output_string = ''

    for match in data["matches"]:
        for game in match:
            output_string += '<u>' + match[game]["teams"]["home"] + ' vs ' + match[game]["teams"]["away"] + '</u><br>'
            for bet in match[game]["bets"]:
                output_string += bet + '<br>'
            output_string += '<br>'
    return output_string

def parse_error (issue, additional_text=''):
    safe_error = html.escape(issue)
    safe_additional_text = html.escape(additional_text)
    return f'{ safe_error } { safe_additional_text }'