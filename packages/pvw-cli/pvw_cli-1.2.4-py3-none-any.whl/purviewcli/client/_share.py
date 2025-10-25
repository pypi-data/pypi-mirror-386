from .endpoint import Endpoint, decorator, get_json
from .endpoints import ENDPOINTS, DATAMAP_API_VERSION, format_endpoint, get_api_version_params

class Share(Endpoint):
    def __init__(self):
        Endpoint.__init__(self)
        self.app = 'share'

    # Accepted Sent Shares
    @decorator
    def shareListAcceptedShares(self, args):
        sentShareName = args['--sentShareName']
        self.params = get_api_version_params('datamap')
        self.method = "GET"
        self.endpoint = ENDPOINTS['share']['accepted_sent_shares'].format(sentShareName=sentShareName)

    @decorator
    def shareGetAcceptedShare(self, args):
        sentShareName = args['--sentShareName']
        acceptedSentShareName = args['--acceptedSentShareName']
        self.params = get_api_version_params('datamap')
        self.method = "GET"
        self.endpoint = ENDPOINTS['share']['accepted_sent_share'].format(
            sentShareName=sentShareName,
            acceptedSentShareName=acceptedSentShareName
        )

    @decorator
    def shareReinstateAcceptedShare(self, args):
        sentShareName = args['--sentShareName']
        acceptedSentShareName = args['--acceptedSentShareName']
        self.params = get_api_version_params('datamap')
        self.method = "POST"
        self.endpoint = ENDPOINTS['share']['reinstate_accepted_share'].format(
            sentShareName=sentShareName,
            acceptedSentShareName=acceptedSentShareName
        )
        self.payload = get_json(args, '--payloadFile')

    @decorator
    def shareRevokeAcceptedShare(self, args):
        sentShareName = args['--sentShareName']
        acceptedSentShareName = args['--acceptedSentShareName']
        self.params = get_api_version_params('datamap')
        self.method = "POST"
        self.endpoint = ENDPOINTS['share']['revoke_accepted_share'].format(
            sentShareName=sentShareName,
            acceptedSentShareName=acceptedSentShareName
        )

    @decorator
    def shareUpdateExpirationAcceptedShare(self, args):
        sentShareName = args['--sentShareName']
        acceptedSentShareName = args['--acceptedSentShareName']
        self.params = get_api_version_params('datamap')
        self.method = "POST"
        self.endpoint = ENDPOINTS['share']['update_expiration_accepted_share'].format(
            sentShareName=sentShareName,
            acceptedSentShareName=acceptedSentShareName
        )
        self.payload = get_json(args, '--payloadFile')

    @decorator
    def shareListAssetMappings(self, args):
        receivedShareName = args['--receivedShareName']
        self.params = get_api_version_params('datamap')
        self.method = "GET"
        self.endpoint = ENDPOINTS['share']['asset_mappings'].format(receivedShareName=receivedShareName)

    @decorator
    def shareCreateAssetMapping(self, args):
        receivedShareName = args['--receivedShareName']
        assetMappingName = args['--assetMappingName']
        self.params = get_api_version_params('datamap')
        self.method = "PUT"
        self.endpoint = ENDPOINTS['share']['asset_mapping'].format(
            receivedShareName=receivedShareName,
            assetMappingName=assetMappingName
        )
        self.payload = get_json(args, '--payloadFile')

    @decorator
    def shareDeleteAssetMapping(self, args):
        receivedShareName = args['--receivedShareName']
        assetMappingName = args['--assetMappingName']
        self.params = get_api_version_params('datamap')
        self.method = "DELETE"
        self.endpoint = ENDPOINTS['share']['asset_mapping'].format(
            receivedShareName=receivedShareName,
            assetMappingName=assetMappingName
        )

    @decorator
    def shareGetAssetMapping(self, args):
        receivedShareName = args['--receivedShareName']
        assetMappingName = args['--assetMappingName']
        self.params = get_api_version_params('datamap')
        self.method = "GET"
        self.endpoint = ENDPOINTS['share']['asset_mapping'].format(
            receivedShareName=receivedShareName,
            assetMappingName=assetMappingName
        )

    @decorator
    def shareListAssets(self, args):
        sentShareName = args['--sentShareName']
        self.params = get_api_version_params('datamap')
        self.method = "GET"
        self.endpoint = ENDPOINTS['share']['assets'].format(sentShareName=sentShareName)

    @decorator
    def shareCreateAsset(self, args):
        sentShareName = args['--sentShareName']
        assetName = args['--assetName']
        self.params = get_api_version_params('datamap')
        self.method = "PUT"
        self.endpoint = ENDPOINTS['share']['asset'].format(
            sentShareName=sentShareName,
            assetName=assetName
        )
        self.payload = get_json(args, '--payloadFile')

    @decorator
    def shareDeleteAsset(self, args):
        sentShareName = args['--sentShareName']
        assetName = args['--assetName']
        self.params = get_api_version_params('datamap')
        self.method = "DELETE"
        self.endpoint = ENDPOINTS['share']['asset'].format(
            sentShareName=sentShareName,
            assetName=assetName
        )

    @decorator
    def shareGetAsset(self, args):
        sentShareName = args['--sentShareName']
        assetName = args['--assetName']
        self.params = get_api_version_params('datamap')
        self.method = "GET"
        self.endpoint = ENDPOINTS['share']['asset'].format(
            sentShareName=sentShareName,
            assetName=assetName
        )

    @decorator
    def shareActivateEmail(self, args):
        self.params = get_api_version_params('datamap')
        self.method = "POST"
        self.endpoint = ENDPOINTS['share']['activate_email']
        self.payload = get_json(args, '--payloadFile')

    @decorator
    def shareRegisterEmail(self, args):
        self.params = get_api_version_params('datamap')
        self.method = "POST"
        self.endpoint = "/registerEmail"

    @decorator
    def shareListReceivedAssets(self, args):
        receivedShareName = args['--receivedShareName']
        self.params = get_api_version_params('datamap')
        self.method = "GET"
        self.endpoint = f"/receivedShares/{receivedShareName}/receivedAssets"

    @decorator
    def shareListReceivedInvitations(self, args):
        self.params = get_api_version_params('datamap')
        self.method = "GET"
        self.endpoint = "/receivedInvitations"

    @decorator
    def shareGetReceivedInvitation(self, args):
        receivedInvitationName = args['--invitationName']
        self.params = get_api_version_params('datamap')
        self.method = "GET"
        self.endpoint = f"/receivedInvitations/{receivedInvitationName}"

    @decorator
    def shareRejectReceivedInvitation(self, args):
        receivedInvitationName = args['--invitationName']
        self.params = get_api_version_params('datamap')
        self.method = "POST"
        self.endpoint = f"/receivedInvitations/{receivedInvitationName}:reject"
        self.payload = get_json(args, '--payloadFile')

    @decorator
    def shareListReceivedShares(self, args):
        self.params = get_api_version_params('datamap')
        self.method = "GET"
        self.endpoint = "/receivedShares"

    @decorator
    def shareCreateReceivedShare(self, args):
        receivedShareName = args['--receivedShareName']
        self.params = get_api_version_params('datamap')
        self.method = "PUT"
        self.endpoint = f"/receivedShares/{receivedShareName}"
        self.payload = get_json(args, '--payloadFile')

    @decorator
    def shareDeleteReceivedShare(self, args):
        receivedShareName = args['--receivedShareName']
        self.params = get_api_version_params('datamap')
        self.method = "DELETE"
        self.endpoint = f"/receivedShares/{receivedShareName}"

    @decorator
    def shareGetReceivedShare(self, args):
        receivedShareName = args['--receivedShareName']
        self.params = get_api_version_params('datamap')
        self.method = "GET"
        self.endpoint = f"/receivedShares/{receivedShareName}"

    @decorator
    def shareListSentInvitations(self, args):
        sentShareName = args['--sentShareName']
        self.params = get_api_version_params('datamap')
        self.method = "GET"
        self.endpoint = f"/sentShares/{sentShareName}/sentShareInvitations"

    @decorator
    def shareCreateSentInvitation(self, args):
        sentShareName = args['--sentShareName']
        sentShareInvitationName = args['--invitationName']
        self.params = get_api_version_params('datamap')
        self.method = "PUT"
        self.endpoint = f"/sentShares/{sentShareName}/sentShareInvitations/{sentShareInvitationName}"
        self.payload = get_json(args, '--payloadFile')

    @decorator
    def shareDeleteSentInvitation(self, args):
        sentShareName = args['--sentShareName']
        sentShareInvitationName = args['--invitationName']
        self.params = get_api_version_params('datamap')
        self.method = "DELETE"
        self.endpoint = f"/sentShares/{sentShareName}/sentShareInvitations/{sentShareInvitationName}"

    @decorator
    def shareGetSentInvitation(self, args):
        sentShareName = args['--sentShareName']
        sentShareInvitationName = args['--invitationName']
        self.params = get_api_version_params('datamap')
        self.method = "GET"
        self.endpoint = f"/sentShares/{sentShareName}/sentShareInvitations/{sentShareInvitationName}"

    @decorator
    def shareListSentShares(self, args):
        self.params = get_api_version_params('datamap')
        self.method = "GET"
        self.endpoint = "/sentShares"

    @decorator
    def shareCreateSentShare(self, args):
        sentShareName = args['--sentShareName']
        self.params = get_api_version_params('datamap')
        self.method = "PUT"
        self.endpoint = f"/sentShares/{sentShareName}"
        self.payload = get_json(args, '--payloadFile')

    @decorator
    def shareDeleteSentShare(self, args):
        sentShareName = args['--sentShareName']
        self.params = get_api_version_params('datamap')
        self.method = "DELETE"
        self.endpoint = f"/sentShares/{sentShareName}"

    @decorator
    def shareGetSentShare(self, args):
        sentShareName = args['--sentShareName']
        self.params = get_api_version_params('datamap')
        self.method = "GET"
        self.endpoint = f"/sentShares/{sentShareName}"
