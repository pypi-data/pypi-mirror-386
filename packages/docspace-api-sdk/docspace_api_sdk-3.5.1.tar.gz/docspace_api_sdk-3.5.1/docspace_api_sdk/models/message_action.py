#
# (c) Copyright Ascensio System SIA 2025
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#



from __future__ import annotations
import json
from enum import Enum
from typing_extensions import Self


class MessageAction(int, Enum):
    """
    [1000 - Login success, 1001 - Login success via social account, 1002 - Login fail invalid combination, 1003 - Login fail social account not found, 1004 - Login fail disabled profile, 1005 - Login fail, 1006 - Logout, 1007 - Login success via sms, 1008 - Login fail via sms, 1009 - Login fail ip security, 1010 - Login success via api, 1011 - Login success via social app, 1012 - Login success via api sms, 1013 - Login fail via api, 1014 - Login fail via api sms, 1015 - Login success via SSO, 1016 - Session started, 1017 - Session completed, 1018 - Login fail via SSO, 1019 - Login success via api social account, 1020 - Login fail via api social account, 1021 - Login succes via tfa app, 1022 - Login fail via Tfa app, 1023 - Login fail brute force, 1024 - Login success via api tfa, 1025 - Login fail via api tfa, 1026 - Login fail recaptcha, 1027 - Authorization link activated, 1028 - Login success via OAuth 2.0, 1029 - Login success via login and password, 4000 - User created, 4001 - Guest created, 4002 - User created via invite, 4003 - Guest created via invite, 4004 - User activated, 4005 - Guest activated, 4006 - User updated, 4007 - User updated language, 4008 - User added avatar, 4009 - User deleted avatar, 4010 - User updated avatar thumbnails, 4011 - User linked social account, 4012 - User unlinked social account, 4013 - User sent activation instructions, 4014 - User sent email change instructions, 4015 - User sent password change instructions, 4016 - User sent delete instructions, 4017 - User updated password, 4018 - User deleted, 4019 - Users updated type, 4020 - Users updated status, 4021 - Users sent activation instructions, 4022 - Users deleted, 4023 - Sent invite instructions, 4024 - User imported, 4025 - Guest imported, 4026 - Group created, 4027 - Group updated, 4028 - Group deleted, 4029 - User updated mobile number, 4030 - User data reassigns, 4031 - User data removing, 4032 - User connected tfa app, 4033 - User disconnected tfa app, 4034 - User logout active connections, 4035 - User logout active connection, 4036 - User logout active connections for user, 4037 - Send join invite, 5000 - File created, 5001 - File renamed, 5002 - File updated, 5003 - File created version, 5004 - File deleted version, 5005 - File updated revision comment, 5006 - File locked, 5007 - File unlocked, 5008 - File updated access, 5009 - File downloaded, 5010 - File downloaded as, 5011 - File uploaded, 5012 - File imported, 5013 - File copied, 5014 - File copied with overwriting, 5015 - File moved, 5016 - File moved with overwriting, 5017 - File moved to trash, 5018 - File deleted, 5019 - Folder created, 5020 - Folder renamed, 5021 - Folder updated access, 5022 - Folder copied, 5023 - Folder copied with overwriting, 5024 - Folder moved, 5025 - Folder moved with overwriting, 5026 - Folder moved to trash, 5027 - Folder deleted, 5028 - ThirdParty created, 5029 - ThirdParty updated, 5030 - ThirdParty deleted, 5031 - Documents ThirdParty settings updated, 5032 - Documents overwriting settings updated, 5033 - Documents uploading formats settings updated, 5034 - User file updated, 5035 - File converted, 5036 - File send access link, 5037 - Document service location setting, 5038 - Authorization keys setting, 5039 - Full text search setting, 5040 - Start transfer setting, 5041 - Start backup setting, 5042 - License key uploaded, 5043 - File change owner, 5044 - File restore version, 5045 - Document send to sign, 5046 - Document sign complete, 5047 - User updated email, 5048 - Documents store forcesave, 5049 - Documents forcesave, 5050 - Start storage encryption, 5051 - Privacy room enable, 5052 - Privacy room disable, 5053 - Start storage decryption, 5054 - File opened for change, 5055 - File marked as favorite, 5056 - File removed from favorite, 5057 - Folder downloaded, 5058 - File removed from list, 5059 - Folder removed from list, 5060 - File external link access updated, 5061 - Trash emptied, 5062 - File revision downloaded, 5063 - File marked as read, 5064 - File readed, 5065 - Folder marked as read, 5066 - Folder updated access for, 5068 - File updated access for, 5069 - Documents external share settings updated, 5070 - Room created, 5071 - Room renamed, 5072 - Room archived, 5073 - Room unarchived, 5074 - Room deleted, 5075 - Room update access for user, 5076 - Tag created, 5077 - Tags deleted, 5078 - Added room tags, 5079 - Deleted room tags, 5080 - Room logo created, 5081 - Room logo deleted, 5082 - Room invitation link updated, 5083 - Documents keep new file name settings updated, 5084 - Room remove user, 5085 - Room create user, 5086 - Room invitation link created, 5087 - Room invitation link deleted, 5088 - Room external link created, 5089 - Room external link updated, 5090 - Room external link deleted, 5091 - File external link created, 5092 - File external link updated, 5093 - File external link deleted, 5094 - Room group added, 5095 - Room update access for group, 5096 - Room group remove, 5097 - Room external link revoked, 5098 - Room external link renamed, 5099 - File uploaded with overwriting, 5100 - Room copied, 5101 - Documents display file extension updated, 5102 - Room color changed, 5103 - Room cover changed, 5104 - Room indexing changed, 5105 - Room deny download changed, 5106 - Room index export saved, 5107 - Folder index changed, 5108 - Folder index reordered, 5109 - Room deny download enabled, 5110 - Room deny download disabled, 5111 - File index changed, 5112 - Room watermark set, 5113 - Room watermark disabled, 5114 - Room index export saved, 5115 - Room indexing disabled, 5116 - Room life time set, 5117 - Room life time disabled, 5118 - Room invite resend, 5119 - File version deleted, 5120 - File custom filter enabled, 5121 - File custom filter disabled, 5122 - Folder external link created, 5123 - Folder external link updated, 5124 - Folder external link deleted, 5150 - Form started to fill, 5151 - Form partially filled, 5152 - Form completely filled, 5153 - Form stopped, 5501 - Ldap enabled, 5502 - Ldap disabled, 5503 - LDAP synchronization completed, 6000 - Language settings updated, 6001 - Time zone settings updated, 6002 - Dns settings updated, 6003 - Trusted mail domain settings updated, 6004 - Password strength settings updated, 6005 - Two factor authentication settings updated, 6006 - Administrator message settings updated, 6007 - Default start page settings updated, 6008 - Products list updated, 6009 - Administrator added, 6010 - Administrator opened full access, 6011 - Administrator deleted, 6012 - Users opened product access, 6013 - Groups opened product access, 6014 - Product access opened, 6015 - Product access restricted, 6016 - Product added administrator, 6017 - Product deleted administrator, 6018 - Greeting settings updated, 6019 - Team template changed, 6020 - Color theme changed, 6021 - Owner sent change owner instructions, 6022 - Owner updated, 6023 - Owner sent portal deactivation instructions, 6024 - Owner sent portal delete instructions, 6025 - Portal deactivated, 6026 - Portal deleted, 6027 - Login history report downloaded, 6028 - Audit trail report downloaded, 6029 - SSO enabled, 6030 - SSO disabled, 6031 - Portal access settings updated, 6032 - Cookie settings updated, 6033 - Mail service settings updated, 6034 - Custom navigation settings updated, 6035 - Audit settings updated, 6036 - Two factor authentication disabled, 6037 - Two factor authentication enabled by sms, 6038 - Two factor authentication enabled by tfa app, 6039 - Portal renamed, 6040 - Quota per room changed, 6041 - Quota per room disabled, 6042 - Quota per user changed, 6043 - Quota per user disabled, 6044 - Quota per portal changed, 6045 - Quota per portal disabled, 6046 - Form submit, 6047 - Form opened for filling, 6048 - Custom quota per room default, 6049 - Custom quota per room changed, 6050 - Custom quota per room disabled, 6051 - Custom quota per user default, 6052 - Custom quota per user changed, 6053 - Custom quota per user disabled, 6054 - DevTools access settings changed, 6055 - Webhook created, 6056 - Webhook updated, 6057 - Webhook deleted, 6058 - Created api key, 6059 - Update api key, 6060 - Deleted User api key, 6061 - Customer wallet topped up, 6062 - Customer operation performed, 6063 - Customer operations report downloaded, 6064 - Customer wallet top up settings updated, 6065 - Customer subscription updated, 6066 - Promotional banners visibility settings changed, 6067 - Customer wallet services settings updated, 7000 - Contact admin mail sent, 7001 - Room invite link used, 7002 - User created and added to room, 7003 - Guest created and added to room, 7004 - Contact sales mail sent, 9901 - Create client, 9902 - Update client, 9903 - Regenerate secret, 9904 - Delete client, 9905 - Change client activation, 9906 - Change client visibility, 9907 - Revoke user client, 9908 - Generate authorization code token, 9909 - Generate personal access token, -1 - None]
    """

    """
    allowed enum values
    """
    LoginSuccess = 1000
    LoginSuccessViaSocialAccount = 1001
    LoginFailInvalidCombination = 1002
    LoginFailSocialAccountNotFound = 1003
    LoginFailDisabledProfile = 1004
    LoginFail = 1005
    Logout = 1006
    LoginSuccessViaSms = 1007
    LoginFailViaSms = 1008
    LoginFailIpSecurity = 1009
    LoginSuccessViaApi = 1010
    LoginSuccessViaSocialApp = 1011
    LoginSuccessViaApiSms = 1012
    LoginFailViaApi = 1013
    LoginFailViaApiSms = 1014
    LoginSuccessViaSSO = 1015
    SessionStarted = 1016
    SessionCompleted = 1017
    LoginFailViaSSO = 1018
    LoginSuccessViaApiSocialAccount = 1019
    LoginFailViaApiSocialAccount = 1020
    LoginSuccesViaTfaApp = 1021
    LoginFailViaTfaApp = 1022
    LoginFailBruteForce = 1023
    LoginSuccessViaApiTfa = 1024
    LoginFailViaApiTfa = 1025
    LoginFailRecaptcha = 1026
    AuthLinkActivated = 1027
    LoginSuccessViaOAuth = 1028
    LoginSuccessViaPassword = 1029
    UserCreated = 4000
    GuestCreated = 4001
    UserCreatedViaInvite = 4002
    GuestCreatedViaInvite = 4003
    UserActivated = 4004
    GuestActivated = 4005
    UserUpdated = 4006
    UserUpdatedLanguage = 4007
    UserAddedAvatar = 4008
    UserDeletedAvatar = 4009
    UserUpdatedAvatarThumbnails = 4010
    UserLinkedSocialAccount = 4011
    UserUnlinkedSocialAccount = 4012
    UserSentActivationInstructions = 4013
    UserSentEmailChangeInstructions = 4014
    UserSentPasswordChangeInstructions = 4015
    UserSentDeleteInstructions = 4016
    UserUpdatedPassword = 4017
    UserDeleted = 4018
    UsersUpdatedType = 4019
    UsersUpdatedStatus = 4020
    UsersSentActivationInstructions = 4021
    UsersDeleted = 4022
    SentInviteInstructions = 4023
    UserImported = 4024
    GuestImported = 4025
    GroupCreated = 4026
    GroupUpdated = 4027
    GroupDeleted = 4028
    UserUpdatedMobileNumber = 4029
    UserDataReassigns = 4030
    UserDataRemoving = 4031
    UserConnectedTfaApp = 4032
    UserDisconnectedTfaApp = 4033
    UserLogoutActiveConnections = 4034
    UserLogoutActiveConnection = 4035
    UserLogoutActiveConnectionsForUser = 4036
    SendJoinInvite = 4037
    FileCreated = 5000
    FileRenamed = 5001
    FileUpdated = 5002
    FileCreatedVersion = 5003
    FileDeletedVersion = 5004
    FileUpdatedRevisionComment = 5005
    FileLocked = 5006
    FileUnlocked = 5007
    FileUpdatedAccess = 5008
    FileDownloaded = 5009
    FileDownloadedAs = 5010
    FileUploaded = 5011
    FileImported = 5012
    FileCopied = 5013
    FileCopiedWithOverwriting = 5014
    FileMoved = 5015
    FileMovedWithOverwriting = 5016
    FileMovedToTrash = 5017
    FileDeleted = 5018
    FolderCreated = 5019
    FolderRenamed = 5020
    FolderUpdatedAccess = 5021
    FolderCopied = 5022
    FolderCopiedWithOverwriting = 5023
    FolderMoved = 5024
    FolderMovedWithOverwriting = 5025
    FolderMovedToTrash = 5026
    FolderDeleted = 5027
    ThirdPartyCreated = 5028
    ThirdPartyUpdated = 5029
    ThirdPartyDeleted = 5030
    DocumentsThirdPartySettingsUpdated = 5031
    DocumentsOverwritingSettingsUpdated = 5032
    DocumentsUploadingFormatsSettingsUpdated = 5033
    UserFileUpdated = 5034
    FileConverted = 5035
    FileSendAccessLink = 5036
    DocumentServiceLocationSetting = 5037
    AuthorizationKeysSetting = 5038
    FullTextSearchSetting = 5039
    StartTransferSetting = 5040
    StartBackupSetting = 5041
    LicenseKeyUploaded = 5042
    FileChangeOwner = 5043
    FileRestoreVersion = 5044
    DocumentSendToSign = 5045
    DocumentSignComplete = 5046
    UserUpdatedEmail = 5047
    DocumentsStoreForcesave = 5048
    DocumentsForcesave = 5049
    StartStorageEncryption = 5050
    PrivacyRoomEnable = 5051
    PrivacyRoomDisable = 5052
    StartStorageDecryption = 5053
    FileOpenedForChange = 5054
    FileMarkedAsFavorite = 5055
    FileRemovedFromFavorite = 5056
    FolderDownloaded = 5057
    FileRemovedFromList = 5058
    FolderRemovedFromList = 5059
    FileExternalLinkAccessUpdated = 5060
    TrashEmptied = 5061
    FileRevisionDownloaded = 5062
    FileMarkedAsRead = 5063
    FileReaded = 5064
    FolderMarkedAsRead = 5065
    FolderUpdatedAccessFor = 5066
    FileUpdatedAccessFor = 5068
    DocumentsExternalShareSettingsUpdated = 5069
    RoomCreated = 5070
    RoomRenamed = 5071
    RoomArchived = 5072
    RoomUnarchived = 5073
    RoomDeleted = 5074
    RoomUpdateAccessForUser = 5075
    TagCreated = 5076
    TagsDeleted = 5077
    AddedRoomTags = 5078
    DeletedRoomTags = 5079
    RoomLogoCreated = 5080
    RoomLogoDeleted = 5081
    RoomInvitationLinkUpdated = 5082
    DocumentsKeepNewFileNameSettingsUpdated = 5083
    RoomRemoveUser = 5084
    RoomCreateUser = 5085
    RoomInvitationLinkCreated = 5086
    RoomInvitationLinkDeleted = 5087
    RoomExternalLinkCreated = 5088
    RoomExternalLinkUpdated = 5089
    RoomExternalLinkDeleted = 5090
    FileExternalLinkCreated = 5091
    FileExternalLinkUpdated = 5092
    FileExternalLinkDeleted = 5093
    RoomGroupAdded = 5094
    RoomUpdateAccessForGroup = 5095
    RoomGroupRemove = 5096
    RoomExternalLinkRevoked = 5097
    RoomExternalLinkRenamed = 5098
    FileUploadedWithOverwriting = 5099
    RoomCopied = 5100
    DocumentsDisplayFileExtensionUpdated = 5101
    RoomColorChanged = 5102
    RoomCoverChanged = 5103
    RoomIndexingChanged = 5104
    RoomDenyDownloadChanged = 5105
    RoomIndexExportSaved = 5106
    FolderIndexChanged = 5107
    FolderIndexReordered = 5108
    RoomDenyDownloadEnabled = 5109
    RoomDenyDownloadDisabled = 5110
    FileIndexChanged = 5111
    RoomWatermarkSet = 5112
    RoomWatermarkDisabled = 5113
    RoomIndexingEnabled = 5114
    RoomIndexingDisabled = 5115
    RoomLifeTimeSet = 5116
    RoomLifeTimeDisabled = 5117
    RoomInviteResend = 5118
    FileVersionRemoved = 5119
    FileCustomFilterEnabled = 5120
    FileCustomFilterDisabled = 5121
    FolderExternalLinkCreated = 5122
    FolderExternalLinkUpdated = 5123
    FolderExternalLinkDeleted = 5124
    FormStartedToFill = 5150
    FormPartiallyFilled = 5151
    FormCompletelyFilled = 5152
    FormStopped = 5153
    LdapEnabled = 5501
    LdapDisabled = 5502
    LdapSync = 5503
    LanguageSettingsUpdated = 6000
    TimeZoneSettingsUpdated = 6001
    DnsSettingsUpdated = 6002
    TrustedMailDomainSettingsUpdated = 6003
    PasswordStrengthSettingsUpdated = 6004
    TwoFactorAuthenticationSettingsUpdated = 6005
    AdministratorMessageSettingsUpdated = 6006
    DefaultStartPageSettingsUpdated = 6007
    ProductsListUpdated = 6008
    AdministratorAdded = 6009
    AdministratorOpenedFullAccess = 6010
    AdministratorDeleted = 6011
    UsersOpenedProductAccess = 6012
    GroupsOpenedProductAccess = 6013
    ProductAccessOpened = 6014
    ProductAccessRestricted = 6015
    ProductAddedAdministrator = 6016
    ProductDeletedAdministrator = 6017
    GreetingSettingsUpdated = 6018
    TeamTemplateChanged = 6019
    ColorThemeChanged = 6020
    OwnerSentChangeOwnerInstructions = 6021
    OwnerUpdated = 6022
    OwnerSentPortalDeactivationInstructions = 6023
    OwnerSentPortalDeleteInstructions = 6024
    PortalDeactivated = 6025
    PortalDeleted = 6026
    LoginHistoryReportDownloaded = 6027
    AuditTrailReportDownloaded = 6028
    SSOEnabled = 6029
    SSODisabled = 6030
    PortalAccessSettingsUpdated = 6031
    CookieSettingsUpdated = 6032
    MailServiceSettingsUpdated = 6033
    CustomNavigationSettingsUpdated = 6034
    AuditSettingsUpdated = 6035
    TwoFactorAuthenticationDisabled = 6036
    TwoFactorAuthenticationEnabledBySms = 6037
    TwoFactorAuthenticationEnabledByTfaApp = 6038
    PortalRenamed = 6039
    QuotaPerRoomChanged = 6040
    QuotaPerRoomDisabled = 6041
    QuotaPerUserChanged = 6042
    QuotaPerUserDisabled = 6043
    QuotaPerPortalChanged = 6044
    QuotaPerPortalDisabled = 6045
    FormSubmit = 6046
    FormOpenedForFilling = 6047
    CustomQuotaPerRoomDefault = 6048
    CustomQuotaPerRoomChanged = 6049
    CustomQuotaPerRoomDisabled = 6050
    CustomQuotaPerUserDefault = 6051
    CustomQuotaPerUserChanged = 6052
    CustomQuotaPerUserDisabled = 6053
    DevToolsAccessSettingsChanged = 6054
    WebhookCreated = 6055
    WebhookUpdated = 6056
    WebhookDeleted = 6057
    ApiKeyCreated = 6058
    ApiKeyUpdated = 6059
    ApiKeyDeleted = 6060
    CustomerWalletToppedUp = 6061
    CustomerOperationPerformed = 6062
    CustomerOperationsReportDownloaded = 6063
    CustomerWalletTopUpSettingsUpdated = 6064
    CustomerSubscriptionUpdated = 6065
    BannerSettingsChanged = 6066
    CustomerWalletServicesSettingsUpdated = 6067
    ContactAdminMailSent = 7000
    RoomInviteLinkUsed = 7001
    UserCreatedAndAddedToRoom = 7002
    GuestCreatedAndAddedToRoom = 7003
    ContactSalesMailSent = 7004
    CreateClient = 9901
    UpdateClient = 9902
    RegenerateSecret = 9903
    DeleteClient = 9904
    ChangeClientActivation = 9905
    ChangeClientVisibility = 9906
    RevokeUserClient = 9907
    GenerateAuthorizationCodeToken = 9908
    GeneratePersonalAccessToken = 9909
    None_ = -1

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Create an instance of MessageAction from a JSON string"""
        return cls(json.loads(json_str))


