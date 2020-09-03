from watchman import slack_wrapper, audit


def main():
    slack = slack_wrapper.initiate_slack_connection()
    # print(slack.page_api_search('"access_token:"', 'search.messages', 'messages',  ))
    print(slack_wrapper.find_messages(slack, ["access_token:"],
                                      '(?i)(''|"){0,2}access_token(''|"){0,2}:(\s*)(''|"){0,2}([0-9a-zA-Z!@#$&()\/\-`_.+,"]{30,})(''|"){0,2}',
                                      'testing'))

    print(audit.find_messages(["access_token:"],
                                      '(?i)(''|"){0,2}access_token(''|"){0,2}:(\s*)(''|"){0,2}([0-9a-zA-Z!@#$&()\/\-`_.+,"]{30,})(''|"){0,2}',
                                      'testing'))


if __name__ == '__main__':
    main()
