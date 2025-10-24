
from ..customParserApiClient import createRequest, get_help
from ...Utils.help_formatter import CustomSubparserHelpFormatter

def query_xdr_parse(query_subparsers):
    query_xdr_parser = query_subparsers.add_parser('xdr', 
            help='xdr() query operation', 
            usage=get_help("query_xdr"), formatter_class=CustomSubparserHelpFormatter)

    query_xdr_subparsers = query_xdr_parser.add_subparsers()

    query_xdr_stories_parser = query_xdr_subparsers.add_parser('stories', 
            help='stories() xdr operation', 
            usage=get_help("query_xdr_stories"))

    query_xdr_stories_parser.add_argument('json', nargs='?', default='{}', help='Variables in JSON format (defaults to empty object if not provided).')
    query_xdr_stories_parser.add_argument('-accountID', help='The cato account ID to use for this operation. Overrides the account_id value in the profile setting.  This is use for reseller and MSP accounts to run queries against cato sub accounts from the parent account.')
    query_xdr_stories_parser.add_argument('-t', const=True, default=False, nargs='?', help='Print GraphQL query without sending API call')
    query_xdr_stories_parser.add_argument('-v', const=True, default=False, nargs='?', help='Verbose output')
    query_xdr_stories_parser.add_argument('-p', const=True, default=False, nargs='?', help='Pretty print')
    query_xdr_stories_parser.add_argument('-n', '--stream-events', dest='stream_events', help='Send events over network to host:port TCP')
    query_xdr_stories_parser.add_argument('-z', '--sentinel', dest='sentinel', help='Send events to Sentinel customerid:sharedkey')
    query_xdr_stories_parser.add_argument('-H', '--header', action='append', dest='headers', help='Add custom headers in "Key: Value" format. Can be used multiple times.')
    query_xdr_stories_parser.add_argument('--headers-file', dest='headers_file', help='Load headers from a file. Each line should contain a header in "Key: Value" format.')
    query_xdr_stories_parser.set_defaults(func=createRequest,operation_name='query.xdr.stories')

    query_xdr_story_parser = query_xdr_subparsers.add_parser('story', 
            help='story() xdr operation', 
            usage=get_help("query_xdr_story"))

    query_xdr_story_parser.add_argument('json', nargs='?', default='{}', help='Variables in JSON format (defaults to empty object if not provided).')
    query_xdr_story_parser.add_argument('-accountID', help='The cato account ID to use for this operation. Overrides the account_id value in the profile setting.  This is use for reseller and MSP accounts to run queries against cato sub accounts from the parent account.')
    query_xdr_story_parser.add_argument('-t', const=True, default=False, nargs='?', help='Print GraphQL query without sending API call')
    query_xdr_story_parser.add_argument('-v', const=True, default=False, nargs='?', help='Verbose output')
    query_xdr_story_parser.add_argument('-p', const=True, default=False, nargs='?', help='Pretty print')
    query_xdr_story_parser.add_argument('-n', '--stream-events', dest='stream_events', help='Send events over network to host:port TCP')
    query_xdr_story_parser.add_argument('-z', '--sentinel', dest='sentinel', help='Send events to Sentinel customerid:sharedkey')
    query_xdr_story_parser.add_argument('-H', '--header', action='append', dest='headers', help='Add custom headers in "Key: Value" format. Can be used multiple times.')
    query_xdr_story_parser.add_argument('--headers-file', dest='headers_file', help='Load headers from a file. Each line should contain a header in "Key: Value" format.')
    query_xdr_story_parser.set_defaults(func=createRequest,operation_name='query.xdr.story')
