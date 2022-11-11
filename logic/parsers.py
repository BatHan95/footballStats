
def parse_bets_for_email(data):

    output_string = ''

    for match in data["matches"]:
        for game in match:
            output_string += match[game]["teams"]["home"] + ' vs ' + match[game]["teams"]["away"] + '<br>'
            for bet in match[game]["bets"]:
                output_string += bet + '<br>'
            output_string += '<br>'
    return output_string
