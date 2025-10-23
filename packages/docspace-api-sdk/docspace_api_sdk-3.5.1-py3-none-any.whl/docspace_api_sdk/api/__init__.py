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



# import apis into api package
from docspace_api_sdk.api.api_keys.api_keys_api import ApiKeysApi
from docspace_api_sdk.api.authentication.authentication_api import AuthenticationApi
from docspace_api_sdk.api.backup.backup_api import BackupApi
from docspace_api_sdk.api.capabilities.capabilities_api import CapabilitiesApi
from docspace_api_sdk.api.files.files_api import FilesApi
from docspace_api_sdk.api.files.folders_api import FoldersApi
from docspace_api_sdk.api.files.operations_api import OperationsApi
from docspace_api_sdk.api.files.quota_api import QuotaApi
from docspace_api_sdk.api.files.settings_api import SettingsApi
from docspace_api_sdk.api.files.sharing_api import SharingApi
from docspace_api_sdk.api.files.third_party_integration_api import ThirdPartyIntegrationApi
from docspace_api_sdk.api.group.group_api import GroupApi
from docspace_api_sdk.api.group.search_api import SearchApi
from docspace_api_sdk.api.migration.migration_api import MigrationApi
from docspace_api_sdk.api.o_auth20.authorization_api import AuthorizationApi
from docspace_api_sdk.api.o_auth20.client_management_api import ClientManagementApi
from docspace_api_sdk.api.o_auth20.client_querying_api import ClientQueryingApi
from docspace_api_sdk.api.o_auth20.scope_management_api import ScopeManagementApi
from docspace_api_sdk.api.people.guests_api import GuestsApi
from docspace_api_sdk.api.people.password_api import PasswordApi
from docspace_api_sdk.api.people.photos_api import PhotosApi
from docspace_api_sdk.api.people.profiles_api import ProfilesApi
from docspace_api_sdk.api.people.quota_api import QuotaApi
from docspace_api_sdk.api.people.search_api import SearchApi
from docspace_api_sdk.api.people.theme_api import ThemeApi
from docspace_api_sdk.api.people.third_party_accounts_api import ThirdPartyAccountsApi
from docspace_api_sdk.api.people.user_data_api import UserDataApi
from docspace_api_sdk.api.people.user_status_api import UserStatusApi
from docspace_api_sdk.api.people.user_type_api import UserTypeApi
from docspace_api_sdk.api.portal.guests_api import GuestsApi
from docspace_api_sdk.api.portal.payment_api import PaymentApi
from docspace_api_sdk.api.portal.quota_api import QuotaApi
from docspace_api_sdk.api.portal.settings_api import SettingsApi
from docspace_api_sdk.api.portal.users_api import UsersApi
from docspace_api_sdk.api.rooms.rooms_api import RoomsApi
from docspace_api_sdk.api.security.access_to_dev_tools_api import AccessToDevToolsApi
from docspace_api_sdk.api.security.active_connections_api import ActiveConnectionsApi
from docspace_api_sdk.api.security.audit_trail_data_api import AuditTrailDataApi
from docspace_api_sdk.api.security.banners_visibility_api import BannersVisibilityApi
from docspace_api_sdk.api.security.csp_api import CSPApi
from docspace_api_sdk.api.security.firebase_api import FirebaseApi
from docspace_api_sdk.api.security.login_history_api import LoginHistoryApi
from docspace_api_sdk.api.security.o_auth2_api import OAuth2Api
from docspace_api_sdk.api.security.smtp_settings_api import SMTPSettingsApi
from docspace_api_sdk.api.settings.access_to_dev_tools_api import AccessToDevToolsApi
from docspace_api_sdk.api.settings.authorization_api import AuthorizationApi
from docspace_api_sdk.api.settings.banners_visibility_api import BannersVisibilityApi
from docspace_api_sdk.api.settings.common_settings_api import CommonSettingsApi
from docspace_api_sdk.api.settings.cookies_api import CookiesApi
from docspace_api_sdk.api.settings.encryption_api import EncryptionApi
from docspace_api_sdk.api.settings.greeting_settings_api import GreetingSettingsApi
from docspace_api_sdk.api.settings.ip_restrictions_api import IPRestrictionsApi
from docspace_api_sdk.api.settings.license_api import LicenseApi
from docspace_api_sdk.api.settings.login_settings_api import LoginSettingsApi
from docspace_api_sdk.api.settings.messages_api import MessagesApi
from docspace_api_sdk.api.settings.notifications_api import NotificationsApi
from docspace_api_sdk.api.settings.owner_api import OwnerApi
from docspace_api_sdk.api.settings.quota_api import QuotaApi
from docspace_api_sdk.api.settings.rebranding_api import RebrandingApi
from docspace_api_sdk.api.settings.sso_api import SSOApi
from docspace_api_sdk.api.settings.security_api import SecurityApi
from docspace_api_sdk.api.settings.statistics_api import StatisticsApi
from docspace_api_sdk.api.settings.storage_api import StorageApi
from docspace_api_sdk.api.settings.tfa_settings_api import TFASettingsApi
from docspace_api_sdk.api.settings.telegram_api import TelegramApi
from docspace_api_sdk.api.settings.webhooks_api import WebhooksApi
from docspace_api_sdk.api.settings.webplugins_api import WebpluginsApi
from docspace_api_sdk.api.third_party.third_party_api import ThirdPartyApi

