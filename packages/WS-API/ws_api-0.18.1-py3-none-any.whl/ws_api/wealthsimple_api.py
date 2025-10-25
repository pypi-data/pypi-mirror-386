from datetime import datetime, timedelta

import re
import requests
import uuid
from typing import Optional, Callable, Any

from ws_api.exceptions import CurlException, LoginFailedException, ManualLoginRequired, OTPRequiredException, UnexpectedException, WSApiException
from ws_api.session import WSAPISession
from inspect import signature


class WealthsimpleAPIBase:
    OAUTH_BASE_URL = 'https://api.production.wealthsimple.com/v1/oauth/v2'
    GRAPHQL_URL = 'https://my.wealthsimple.com/graphql'
    GRAPHQL_VERSION = '12'

    GRAPHQL_QUERIES = {
        'FetchAllAccountFinancials': "query FetchAllAccountFinancials($identityId: ID!, $startDate: Date, $pageSize: Int = 25, $cursor: String) {\n  identity(id: $identityId) {\n    id\n    ...AllAccountFinancials\n    __typename\n  }\n}\n\nfragment AllAccountFinancials on Identity {\n  accounts(filter: {}, first: $pageSize, after: $cursor) {\n    pageInfo {\n      hasNextPage\n      endCursor\n      __typename\n    }\n    edges {\n      cursor\n      node {\n        ...AccountWithFinancials\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment AccountWithFinancials on Account {\n  ...AccountWithLink\n  ...AccountFinancials\n  __typename\n}\n\nfragment AccountWithLink on Account {\n  ...Account\n  linkedAccount {\n    ...Account\n    __typename\n  }\n  __typename\n}\n\nfragment Account on Account {\n  ...AccountCore\n  custodianAccounts {\n    ...CustodianAccount\n    __typename\n  }\n  __typename\n}\n\nfragment AccountCore on Account {\n  id\n  archivedAt\n  branch\n  closedAt\n  createdAt\n  cacheExpiredAt\n  currency\n  requiredIdentityVerification\n  unifiedAccountType\n  supportedCurrencies\n  nickname\n  status\n  accountOwnerConfiguration\n  accountFeatures {\n    ...AccountFeature\n    __typename\n  }\n  accountOwners {\n    ...AccountOwner\n    __typename\n  }\n  type\n  __typename\n}\n\nfragment AccountFeature on AccountFeature {\n  name\n  enabled\n  __typename\n}\n\nfragment AccountOwner on AccountOwner {\n  accountId\n  identityId\n  accountNickname\n  clientCanonicalId\n  accountOpeningAgreementsSigned\n  name\n  email\n  ownershipType\n  activeInvitation {\n    ...AccountOwnerInvitation\n    __typename\n  }\n  sentInvitations {\n    ...AccountOwnerInvitation\n    __typename\n  }\n  __typename\n}\n\nfragment AccountOwnerInvitation on AccountOwnerInvitation {\n  id\n  createdAt\n  inviteeName\n  inviteeEmail\n  inviterName\n  inviterEmail\n  updatedAt\n  sentAt\n  status\n  __typename\n}\n\nfragment CustodianAccount on CustodianAccount {\n  id\n  branch\n  custodian\n  status\n  updatedAt\n  __typename\n}\n\nfragment AccountFinancials on Account {\n  id\n  custodianAccounts {\n    id\n    branch\n    financials {\n      current {\n        ...CustodianAccountCurrentFinancialValues\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  financials {\n    currentCombined {\n      id\n      ...AccountCurrentFinancials\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment CustodianAccountCurrentFinancialValues on CustodianAccountCurrentFinancialValues {\n  deposits {\n    ...Money\n    __typename\n  }\n  earnings {\n    ...Money\n    __typename\n  }\n  netDeposits {\n    ...Money\n    __typename\n  }\n  netLiquidationValue {\n    ...Money\n    __typename\n  }\n  withdrawals {\n    ...Money\n    __typename\n  }\n  __typename\n}\n\nfragment Money on Money {\n  amount\n  cents\n  currency\n  __typename\n}\n\nfragment AccountCurrentFinancials on AccountCurrentFinancials {\n  id\n  netLiquidationValue {\n    ...Money\n    __typename\n  }\n  netDeposits {\n    ...Money\n    __typename\n  }\n  simpleReturns(referenceDate: $startDate) {\n    ...SimpleReturns\n    __typename\n  }\n  totalDeposits {\n    ...Money\n    __typename\n  }\n  totalWithdrawals {\n    ...Money\n    __typename\n  }\n  __typename\n}\n\nfragment SimpleReturns on SimpleReturns {\n  amount {\n    ...Money\n    __typename\n  }\n  asOf\n  rate\n  referenceDate\n  __typename\n}",
        'FetchActivityFeedItems': "query FetchActivityFeedItems($first: Int, $cursor: Cursor, $condition: ActivityCondition, $orderBy: [ActivitiesOrderBy!] = OCCURRED_AT_DESC) {\n  activityFeedItems(\n    first: $first\n    after: $cursor\n    condition: $condition\n    orderBy: $orderBy\n  ) {\n    edges {\n      node {\n        ...Activity\n        __typename\n      }\n      __typename\n    }\n    pageInfo {\n      hasNextPage\n      endCursor\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment Activity on ActivityFeedItem {\n  accountId\n  aftOriginatorName\n  aftTransactionCategory\n  aftTransactionType\n  amount\n  amountSign\n  assetQuantity\n  assetSymbol\n  canonicalId\n  currency\n  eTransferEmail\n  eTransferName\n  externalCanonicalId\n  identityId\n  institutionName\n  occurredAt\n  p2pHandle\n  p2pMessage\n  spendMerchant\n  securityId\n  billPayCompanyName\n  billPayPayeeNickname\n  redactedExternalAccountNumber\n  opposingAccountId\n  status\n  subType\n  type\n  strikePrice\n  contractType\n  expiryDate\n  chequeNumber\n  provisionalCreditAmount\n  primaryBlocker\n  interestRate\n  frequency\n  counterAssetSymbol\n  rewardProgram\n  counterPartyCurrency\n  counterPartyCurrencyAmount\n  counterPartyName\n  fxRate\n  fees\n  reference\n  __typename\n}",
        'FetchSecuritySearchResult': "query FetchSecuritySearchResult($query: String!) {\n  securitySearch(input: {query: $query}) {\n    results {\n      ...SecuritySearchResult\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment SecuritySearchResult on Security {\n  id\n  buyable\n  status\n  stock {\n    symbol\n    name\n    primaryExchange\n    __typename\n  }\n  securityGroups {\n    id\n    name\n    __typename\n  }\n  quoteV2 {\n    ... on EquityQuote {\n      marketStatus\n      __typename\n    }\n    __typename\n  }\n  __typename\n}",
        'FetchSecurityHistoricalQuotes': "query FetchSecurityHistoricalQuotes($id: ID!, $timerange: String! = \"1d\") {\n  security(id: $id) {\n    id\n    historicalQuotes(timeRange: $timerange) {\n      ...HistoricalQuote\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment HistoricalQuote on HistoricalQuote {\n  adjustedPrice\n  currency\n  date\n  securityId\n  time\n  __typename\n}",
        'FetchAccountsWithBalance': "query FetchAccountsWithBalance($ids: [String!]!, $type: BalanceType!) {\n  accounts(ids: $ids) {\n    ...AccountWithBalance\n    __typename\n  }\n}\n\nfragment AccountWithBalance on Account {\n  id\n  custodianAccounts {\n    id\n    financials {\n      ... on CustodianAccountFinancialsSo {\n        balance(type: $type) {\n          ...Balance\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment Balance on Balance {\n  quantity\n  securityId\n  __typename\n}",
        'FetchSecurityMarketData': "query FetchSecurityMarketData($id: ID!) {\n  security(id: $id) {\n    id\n    ...SecurityMarketData\n    __typename\n  }\n}\n\nfragment SecurityMarketData on Security {\n  id\n  allowedOrderSubtypes\n  marginRates {\n    ...MarginRates\n    __typename\n  }\n  fundamentals {\n    avgVolume\n    high52Week\n    low52Week\n    yield\n    peRatio\n    marketCap\n    currency\n    description\n    __typename\n  }\n  quote {\n    bid\n    ask\n    open\n    high\n    low\n    volume\n    askSize\n    bidSize\n    last\n    lastSize\n    quotedAsOf\n    quoteDate\n    amount\n    previousClose\n    __typename\n  }\n  stock {\n    primaryExchange\n    primaryMic\n    name\n    symbol\n    __typename\n  }\n  __typename\n}\n\nfragment MarginRates on MarginRates {\n  clientMarginRate\n  __typename\n}",
        'FetchFundsTransfer': "query FetchFundsTransfer($id: ID!) {\n  fundsTransfer: funds_transfer(id: $id, include_cancelled: true) {\n    ...FundsTransfer\n    __typename\n  }\n}\n\nfragment FundsTransfer on FundsTransfer {\n  id\n  status\n  cancellable\n  rejectReason: reject_reason\n  schedule {\n    id\n    __typename\n  }\n  source {\n    ...BankAccountOwner\n    __typename\n  }\n  destination {\n    ...BankAccountOwner\n    __typename\n  }\n  __typename\n}\n\nfragment BankAccountOwner on BankAccountOwner {\n  bankAccount: bank_account {\n    ...BankAccount\n    __typename\n  }\n  __typename\n}\n\nfragment BankAccount on BankAccount {\n  id\n  accountName: account_name\n  corporate\n  createdAt: created_at\n  currency\n  institutionName: institution_name\n  jurisdiction\n  nickname\n  type\n  updatedAt: updated_at\n  verificationDocuments: verification_documents {\n    ...BankVerificationDocument\n    __typename\n  }\n  verifications {\n    ...BankAccountVerification\n    __typename\n  }\n  ...CaBankAccount\n  ...UsBankAccount\n  __typename\n}\n\nfragment CaBankAccount on CaBankAccount {\n  accountName: account_name\n  accountNumber: account_number\n  __typename\n}\n\nfragment UsBankAccount on UsBankAccount {\n  accountName: account_name\n  accountNumber: account_number\n  __typename\n}\n\nfragment BankVerificationDocument on VerificationDocument {\n  id\n  acceptable\n  updatedAt: updated_at\n  createdAt: created_at\n  documentId: document_id\n  documentType: document_type\n  rejectReason: reject_reason\n  reviewedAt: reviewed_at\n  reviewedBy: reviewed_by\n  __typename\n}\n\nfragment BankAccountVerification on BankAccountVerification {\n  custodianProcessedAt: custodian_processed_at\n  custodianStatus: custodian_status\n  document {\n    ...BankVerificationDocument\n    __typename\n  }\n  __typename\n}",
        'FetchInstitutionalTransfer': "query FetchInstitutionalTransfer($id: ID!) {\n  accountTransfer(id: $id) {\n    ...InstitutionalTransfer\n    __typename\n  }\n}\n\nfragment InstitutionalTransfer on InstitutionalTransfer {\n  id\n  accountId: account_id\n  state\n  documentId: document_id\n  documentType: document_type\n  expectedCompletionDate: expected_completion_date\n  timelineExpectation: timeline_expectation {\n    lowerBound: lower_bound\n    upperBound: upper_bound\n    __typename\n  }\n  estimatedCompletionMaximum: estimated_completion_maximum\n  estimatedCompletionMinimum: estimated_completion_minimum\n  institutionName: institution_name\n  transferStatus: external_state\n  redactedInstitutionAccountNumber: redacted_institution_account_number\n  expectedValue: expected_value\n  transferType: transfer_type\n  cancellable\n  pdfUrl: pdf_url\n  clientVisibleState: client_visible_state\n  shortStatusDescription: short_status_description\n  longStatusDescription: long_status_description\n  progressPercentage: progress_percentage\n  type\n  rolloverType: rollover_type\n  autoSignatureEligible: auto_signature_eligible\n  parentInstitution: parent_institution {\n    id\n    name\n    __typename\n  }\n  stateHistories: state_histories {\n    id\n    state\n    notes\n    transitionSubmittedBy: transition_submitted_by\n    transitionedAt: transitioned_at\n    transitionCode: transition_code\n    __typename\n  }\n  transferFeeReimbursement: transfer_fee_reimbursement {\n    id\n    feeAmount: fee_amount\n    __typename\n  }\n  docusignSentViaEmail: docusign_sent_via_email\n  clientAccountType: client_account_type\n  primaryClientIdentityId: primary_client_identity_id\n  primaryOwnerSigned: primary_owner_signed\n  secondaryOwnerSigned: secondary_owner_signed\n  __typename\n}",
        'FetchAccountHistoricalFinancials': "query FetchAccountHistoricalFinancials($id: ID!, $currency: Currency!, $startDate: Date, $resolution: DateResolution!, $endDate: Date, $first: Int, $cursor: String) {\n          account(id: $id) {\n            id\n            financials {\n              historicalDaily(\n                currency: $currency\n                startDate: $startDate\n                resolution: $resolution\n                endDate: $endDate\n                first: $first\n                after: $cursor\n              ) {\n                edges {\n                  node {\n                    ...AccountHistoricalFinancials\n                    __typename\n                  }\n                  __typename\n                }\n                pageInfo {\n                  hasNextPage\n                  endCursor\n                  __typename\n                }\n                __typename\n              }\n              __typename\n            }\n            __typename\n          }\n        }\n\n        fragment AccountHistoricalFinancials on AccountHistoricalDailyFinancials {\n          date\n          netLiquidationValueV2 {\n            ...Money\n            __typename\n          }\n          netDepositsV2 {\n            ...Money\n            __typename\n          }\n          __typename\n        }\n\n        fragment Money on Money {\n          amount\n          cents\n          currency\n          __typename\n        }",
        'FetchIdentityHistoricalFinancials': "query FetchIdentityHistoricalFinancials($identityId: ID!, $currency: Currency!, $startDate: Date, $endDate: Date, $first: Int, $cursor: String, $accountIds: [ID!]) {\n      identity(id: $identityId) {\n        id\n        financials(filter: {accounts: $accountIds}) {\n          historicalDaily(\n            currency: $currency\n            startDate: $startDate\n            endDate: $endDate\n            first: $first\n            after: $cursor\n          ) {\n            edges {\n              node {\n                ...IdentityHistoricalFinancials\n                __typename\n              }\n              __typename\n            }\n            pageInfo {\n              hasNextPage\n              endCursor\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n    }\n\n    fragment IdentityHistoricalFinancials on IdentityHistoricalDailyFinancials {\n      date\n      netLiquidationValueV2 {\n        amount\n        currency\n        __typename\n      }\n      netDepositsV2 {\n        amount\n        currency\n        __typename\n      }\n      __typename\n    }",
    }

    def __init__(self, sess: Optional[WSAPISession] = None):
        self.security_market_data_cache_getter = None
        self.security_market_data_cache_setter = None
        self.session = WSAPISession()
        self.start_session(sess)

    user_agent = None

    @staticmethod
    def set_user_agent(user_agent: str):
        WealthsimpleAPI.user_agent = user_agent

    @staticmethod
    def uuidv4() -> str:
        return str(uuid.uuid4())

    def send_http_request(
        self, url: str, method: str = 'POST', data: Optional[dict] = None, headers: Optional[dict] = None, return_headers: bool = False
    ) -> Any:
        headers = headers or {}
        if method == 'POST':
            headers['Content-Type'] = 'application/json'

        if self.session.session_id:
            headers['x-ws-session-id'] = self.session.session_id

        if self.session.access_token and (not data or data.get('grant_type') != 'refresh_token'):
            headers['Authorization'] = f"Bearer {self.session.access_token}"

        if self.session.wssdi:
            headers['x-ws-device-id'] = self.session.wssdi

        if WealthsimpleAPI.user_agent:
            headers['User-Agent'] = WealthsimpleAPI.user_agent

        try:
            response = requests.request(method, url, json=data, headers=headers)

            if return_headers:
                # Combine headers and body as a single string
                headers = '\r\n'.join(f"{k}: {v}" for k, v in response.headers.items())
                return f"{headers}\r\n\r\n{response.text}"

            return response.json()
        except requests.exceptions.RequestException as e:
            raise CurlException(f"HTTP request failed: {e}")

    def send_get(self, url: str, headers: Optional[dict] = None, return_headers: bool = False) -> Any:
        return self.send_http_request(url, 'GET', headers=headers, return_headers=return_headers)

    def send_post(self, url: str, data: dict, headers: Optional[dict] = None, return_headers: bool = False) -> Any:
        return self.send_http_request(url, 'POST', data=data, headers=headers, return_headers=return_headers)

    def start_session(self, sess: WSAPISession = None):
        if sess:
            self.session.access_token = sess.access_token
            self.session.wssdi = sess.wssdi
            self.session.session_id = sess.session_id
            self.session.client_id = sess.client_id
            self.session.refresh_token = sess.refresh_token
            return

        app_js_url = None

        if not self.session.wssdi or not self.session.client_id:
            # Fetch login page
            response = self.send_get('https://my.wealthsimple.com/app/login', return_headers=True)

            for line in response.splitlines():
                # Look for wssdi in set-cookie headers
                if not self.session.wssdi and "set-cookie:" in line.lower():
                    match = re.search(r"wssdi=([a-f0-9]+);", line, re.IGNORECASE)
                    if match:
                        self.session.wssdi = match.group(1)

                if not app_js_url and "<script" in line.lower():
                    match = re.search(r'<script.*src="(.+/app-[a-f0-9]+\.js)', line, re.IGNORECASE)
                    if match:
                        app_js_url = match.group(1)

            if not self.session.wssdi:
                raise UnexpectedException("Couldn't find wssdi in login page response headers.")

        if not self.session.client_id:
            if not app_js_url:
                raise UnexpectedException("Couldn't find app JS URL in login page response body.")

            # Fetch the app JS file
            response = self.send_get(app_js_url, return_headers=True)

            # Look for clientId in the app JS file
            match = re.search(r'production:.*clientId:"([a-f0-9]+)"', response, re.IGNORECASE)
            if match:
                self.session.client_id = match.group(1)

            if not self.session.client_id:
                raise UnexpectedException("Couldn't find clientId in app JS.")

        if not self.session.session_id:
            self.session.session_id = str(uuid.uuid4())

    def check_oauth_token(self, persist_session_fct: Optional[Callable[[WSAPISession, Optional[str]], None]] = None, username = None):
        if self.session.access_token:
            try:
                # noinspection PyUnresolvedReferences
                self.search_security('XEQT')
                return
            except WSApiException as e:
                if e.response['message'] != 'Not Authorized.':
                    raise e
                # Access token expired; try to refresh it below

        if self.session.refresh_token:
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.session.refresh_token,
                'client_id': self.session.client_id,
            }
            headers = {
                'x-wealthsimple-client': '@wealthsimple/wealthsimple',
                'x-ws-profile': 'invest'
            }
            response = self.send_post(f"{self.OAUTH_BASE_URL}/token", data, headers)
            if not 'access_token' in response or not 'refresh_token' in response:
                raise ManualLoginRequired(f"OAuth token invalid and cannot be refreshed: {response['error'] if 'error' in response else 'Invalid response from API'}")
            self.session.access_token = response['access_token']
            self.session.refresh_token = response['refresh_token']
            if persist_session_fct:
                if len(signature(persist_session_fct).parameters) == 2:
                    persist_session_fct(self.session.to_json(), username)
                else:
                    persist_session_fct(self.session.to_json())
            return

        raise ManualLoginRequired("OAuth token invalid and cannot be refreshed.")

    SCOPE_READ_ONLY = 'invest.read trade.read tax.read'
    SCOPE_READ_WRITE = 'invest.read trade.read tax.read invest.write trade.write tax.write'

    def login_internal(self, username: str, password: str, otp_answer: str = None,
                       persist_session_fct: callable = None, scope: str = SCOPE_READ_ONLY) -> WSAPISession:
        data = {
            'grant_type': 'password',
            'username': username,
            'password': password,
            'skip_provision': 'true',
            'scope': scope,
            'client_id': self.session.client_id,
            'otp_claim': None,
        }

        headers = {
            'x-wealthsimple-client': '@wealthsimple/wealthsimple',
            'x-ws-profile': 'undefined'
        }

        if otp_answer:
            headers['x-wealthsimple-otp'] = f"{otp_answer};remember=true"

        # Send the POST request for token
        response_data = self.send_post(
            url=f"{self.OAUTH_BASE_URL}/token",
            data=data,
            headers=headers
        )

        if 'error' in response_data and response_data['error'] == "invalid_grant" and otp_answer is None:
            raise OTPRequiredException("2FA code required")

        if 'error' in response_data:
            raise LoginFailedException("Login failed", response_data)

        # Update the session with the tokens
        self.session.access_token = response_data['access_token']
        self.session.refresh_token = response_data['refresh_token']

        # Persist the session if a persist function is provided
        if persist_session_fct:
            if len(signature(persist_session_fct).parameters) == 2:
                persist_session_fct(self.session.to_json(), username)
            else:
                persist_session_fct(self.session.to_json())

        return self.session

    def do_graphql_query(self, query_name: str, variables: dict, data_response_path: str, expect_type: str,
                         filter_fn: callable = None, load_all_pages: bool = False):
        query = {
            'operationName': query_name,
            'query': self.GRAPHQL_QUERIES[query_name],
            'variables': variables,
        }

        headers = {
            "x-ws-profile": "trade",
            "x-ws-api-version": self.GRAPHQL_VERSION,
            "x-ws-locale": "en-CA",
            "x-platform-os": "web",
        }

        response_data = self.send_post(
            url=self.GRAPHQL_URL,
            data=query,
            headers=headers
        )

        if 'data' not in response_data:
            raise WSApiException(f"GraphQL query failed: {query_name}", response_data)

        data = response_data['data']

        end_cursor = None

        # Access the nested data using the data_response_path
        for key in data_response_path.split('.'):
            if key not in data:
                raise WSApiException(f"GraphQL query failed: {query_name}", response_data)
            data = data[key]
            if hasattr(data, 'pageInfo') and hasattr(data.pageInfo, 'hasNextPage') and data.pageInfo.hasNextPage:
                end_cursor = data.pageInfo.endCursor

        # Ensure the data type matches the expected one (either array or object)
        if (expect_type == 'array' and not isinstance(data, list)) or (
                expect_type == 'object' and not isinstance(data, dict)):
            raise WSApiException(f"GraphQL query failed: {query_name}", response_data)

        # noinspection PyUnboundLocalVariable
        if key == 'edges':
            data = [edge['node'] for edge in data]

        if filter_fn:
            data = list(filter(filter_fn, data))

        if load_all_pages:
            if expect_type != 'array':
                raise UnexpectedException("Can't load all pages for GraphQL queries that do not return arrays")
            if end_cursor:
                variables['cursor'] = end_cursor
                more_data = self.do_graphql_query(query_name, variables, data_response_path, expect_type, filter, True)
                data += more_data

        return data

    def get_token_info(self):
        if not self.session.token_info:
            headers = {
                'x-wealthsimple-client': '@wealthsimple/wealthsimple'
            }
            response = self.send_get(self.OAUTH_BASE_URL + '/token/info', headers=headers)
            self.session.token_info = response
        return self.session.token_info

    @staticmethod
    def login(username: str, password: str, otp_answer: str = None, persist_session_fct: callable = None, scope: str = SCOPE_READ_ONLY):
        ws = WealthsimpleAPI()
        return ws.login_internal(username, password, otp_answer, persist_session_fct, scope)

    @staticmethod
    def from_token(sess: WSAPISession, persist_session_fct: callable = None, username: Optional[str] = None):
        ws = WealthsimpleAPI(sess)
        ws.check_oauth_token(persist_session_fct, username)
        return ws

class WealthsimpleAPI(WealthsimpleAPIBase):
    def __init__(self, sess: WSAPISession = None):
        super().__init__(sess)
        self.account_cache = {}

    def get_accounts(self, open_only=True, use_cache=True):
        cache_key = 'open' if open_only else 'all'
        if not use_cache or cache_key not in self.account_cache:
            filter_fn = (lambda acc: acc.get('status') == 'open') if open_only else None

            accounts = self.do_graphql_query(
                'FetchAllAccountFinancials',
                {
                    'pageSize': 25,
                    'identityId': self.get_token_info().get('identity_canonical_id'),
                },
                'identity.accounts.edges',
                'array',
                filter_fn=filter_fn,
                load_all_pages=True,
            )
            for account in accounts:
                self._account_add_description(account)
            self.account_cache[cache_key] = accounts
        return self.account_cache[cache_key]

    @staticmethod
    def _account_add_description(account):
        account['number'] = account['id']
        # This is the account number visible in the WS app:
        for ca in account['custodianAccounts']:
            if (ca['branch'] in ['WS', 'TR']) and ca['status'] == 'open':
                account['number'] = ca['id']

        # Default
        account['description'] = account['unifiedAccountType']

        if account.get('nickname'):
            account['description'] = account['nickname']
        elif account['unifiedAccountType'] == 'CASH':
            account['description'] = "Cash: joint" if account['accountOwnerConfiguration'] == 'MULTI_OWNER' else "Cash"
        elif account['unifiedAccountType'] == 'SELF_DIRECTED_RRSP':
            account['description'] = f"RRSP: self-directed - {account['currency']}"
        elif account['unifiedAccountType'] == 'MANAGED_RRSP':
            account['description'] = f"RRSP: managed - {account['currency']}"
        elif account['unifiedAccountType'] == 'SELF_DIRECTED_SPOUSAL_RRSP':
            account['description'] = f"RRSP: self-directed spousal - {account['currency']}"
        elif account['unifiedAccountType'] == 'SELF_DIRECTED_TFSA':
            account['description'] = f"TFSA: self-directed - {account['currency']}"
        elif account['unifiedAccountType'] == 'MANAGED_TFSA':
            account['description'] = f"TFSA: managed - {account['currency']}"
        elif account['unifiedAccountType'] == 'SELF_DIRECTED_JOINT_NON_REGISTERED':
            account['description'] = "Non-registered: self-directed - joint"
        elif account['unifiedAccountType'] == 'SELF_DIRECTED_NON_REGISTERED_MARGIN':
            account['description'] = "Non-registered: self-directed margin"
        elif account['unifiedAccountType'] == 'MANAGED_JOINT':
            account['description'] = "Non-registered: managed - joint"
        elif account['unifiedAccountType'] == 'SELF_DIRECTED_CRYPTO':
            account['description'] = "Crypto"
        elif account['unifiedAccountType'] == 'SELF_DIRECTED_RRIF':
             account['description'] = f"RRIF: self-directed - {account['currency']}"
        elif account['unifiedAccountType'] == 'CREDIT_CARD':
             account['description'] = "Credit card"
        # TODO: Add other types as needed

    def get_account_balances(self, account_id):
        accounts = self.do_graphql_query(
            'FetchAccountsWithBalance',
            {
                'type': 'TRADING',
                'ids': [account_id],
            },
            'accounts',
            'array',
        )

        # Extracting balances and returning them in a dictionary
        balances = {}
        for account in accounts[0]['custodianAccounts']:
            for balance in account['financials']['balance']:
                security = balance['securityId']
                if security != 'sec-c-cad' and security != 'sec-c-usd':
                    security = self.security_id_to_symbol(security)
                balances[security] = balance['quantity']

        return balances

    def get_account_historical_financials(self, account_id: str, currency: str = 'CAD', start_date = None, end_date = None, resolution = 'WEEKLY', first = None, cursor = None):
        return self.do_graphql_query(
            'FetchAccountHistoricalFinancials',
            {
                'id': account_id,
                'currency': currency,
                'startDate': start_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ') if start_date else None,
                'endDate': end_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ') if end_date else None,
                'resolution': resolution,
                'first': first,
                'cursor': cursor
            },
            'account.financials.historicalDaily.edges',
            'array',
        )

    def get_identity_historical_financials(self, account_ids = None, currency: str = 'CAD', start_date = None, end_date = None, first = None, cursor = None):
        return self.do_graphql_query(
            'FetchIdentityHistoricalFinancials',
            {
                'identityId': self.get_token_info().get('identity_canonical_id'),
                'currency': currency,
                'startDate': start_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ') if start_date else None,
                'endDate': end_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ') if end_date else None,
                'first': first,
                'cursor': cursor,
                'accountIds': account_ids or [],
            },
            'identity.financials.historicalDaily.edges',
            'array',
        )

    def get_activities(self, account_id, how_many=50, order_by='OCCURRED_AT_DESC', ignore_rejected=True, start_date = None, end_date = None):
        # Calculate the end date for the condition
        end_date = (end_date if end_date else datetime.now() + timedelta(hours=23, minutes=59, seconds=59, milliseconds=999))

        # Filter function to ignore rejected/cancelled activities
        def filter_fn(activity):
            act_type = (activity.get('type', '') or '').upper()
            status = (activity.get('status', '') or '').lower()
            return act_type != 'LEGACY_TRANSFER' and (not ignore_rejected or status == '' or ('rejected' not in status and 'cancelled' not in status))

        activities = self.do_graphql_query(
            'FetchActivityFeedItems',
            {
                'orderBy': order_by,
                'first': how_many,
                'condition': {
                    'startDate': start_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ') if start_date else None,
                    'endDate': end_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                    'accountIds': [account_id],
                },
            },
            'activityFeedItems.edges',
            'array',
            filter_fn = filter_fn,
        )

        for act in activities:
            self._activity_add_description(act)

        return activities

    def _activity_add_description(self, act):
        act['description'] = f"{act['type']}: {act['subType']}"

        if act['type'] == 'INTERNAL_TRANSFER':
            accounts = self.get_accounts(False)
            matching = [acc for acc in accounts if acc['id'] == act['opposingAccountId']]
            target_account = matching.pop() if matching else None
            account_description = (
                f"{target_account['description']} ({target_account['number']})"
                if target_account else
                act['opposingAccountId']
            )
            if act['subType'] == 'SOURCE':
                act['description'] = f"Transfer out: Transfer to Wealthsimple {account_description}"
            else:
                act['description'] = f"Transfer in: Transfer from Wealthsimple {account_description}"

        elif act['type'] in ['DIY_BUY', 'DIY_SELL']:
            verb = act['subType'].replace('_', ' ').capitalize()
            action = 'buy' if act['type'] == 'DIY_BUY' else 'sell'
            security = self.security_id_to_symbol(act['securityId'])
            if act['assetQuantity'] is None:
                act['description'] = (
                    f"{verb}: {action} TBD"
                )
            else:
                act['description'] = (
                    f"{verb}: {action} {float(act['assetQuantity'])} x "
                    f"{security} @ {float(act['amount']) / float(act['assetQuantity'])}"
                )

        elif act['type'] == 'CORPORATE_ACTION' and act['subType'] == 'SUBDIVISION':
            act['description'] = f"Subdivision: Received {act['amount']} shares of {act['assetSymbol']}"

        elif act['type'] in ['DEPOSIT', 'WITHDRAWAL'] and act['subType'] in ['E_TRANSFER', 'E_TRANSFER_FUNDING']:
            direction = 'from' if act['type'] == 'DEPOSIT' else 'to'
            act['description'] = (
                f"Deposit: Interac e-transfer {direction} {act['eTransferName']} {act['eTransferEmail']}"
            )

        elif act['type'] == 'DEPOSIT' and act['subType'] == 'PAYMENT_CARD_TRANSACTION':
            type_ = act['type'].lower().capitalize()
            act['description'] = f"{type_}: Debit card funding"

        elif act['subType'] == 'EFT':
            details = self.get_etf_details(act['externalCanonicalId'])
            type_ = act['type'].lower().capitalize()
            direction = 'from' if act['type'] == 'DEPOSIT' else 'to'
            prop = 'source' if act['type'] == 'DEPOSIT' else 'destination'
            bank_account = details[prop]['bankAccount']
            nickname = bank_account.get('nickname')
            if not nickname:
                nickname = bank_account['accountName']
            act['description'] = (
                f"{type_}: EFT {direction} {nickname} {bank_account['accountNumber']}"
            )

        elif act['type'] == 'REFUND' and act['subType'] == 'TRANSFER_FEE_REFUND':
            act['description'] = "Reimbursement: account transfer fee"

        elif act['type'] == 'INSTITUTIONAL_TRANSFER_INTENT' and act['subType'] == 'TRANSFER_IN':
            details = self.get_transfer_details(act['externalCanonicalId'])
            verb = details['transferType'].replace('_', '-').capitalize()
            act['description'] = (
                f"Institutional transfer: {verb} {details['clientAccountType'].upper()} "
                f"account transfer from {details['institutionName']} "
                f"****{details['redactedInstitutionAccountNumber']}"
            )

        elif act['type'] == 'INTEREST':
            if act['subType'] == 'FPL_INTEREST':
                act['description'] = "Stock Lending Earnings"
            else:
                act['description'] = "Interest"

        elif act['type'] == 'DIVIDEND':
            security = self.security_id_to_symbol(act['securityId'])
            act['description'] = f"Dividend: {security}"

        elif act['type'] == 'FUNDS_CONVERSION':
            act['description'] = f"Funds converted: {act['currency']} from {'USD' if act['currency'] == 'CAD' else 'CAD'}"

        elif act['type'] == 'NON_RESIDENT_TAX':
            act['description'] = "Non-resident tax"

        # Refs:
        #   https://www.payments.ca/payment-resources/iso-20022/automatic-funds-transfer
        #   https://www.payments.ca/compelling-new-evidence-strong-link-between-aft-and-canadas-cheque-decline
        # 2nd ref states: "AFTs are electronic direct credit or direct debit transactions, commonly known in Canada as direct deposits or pre-authorized debits (PADs)."
        elif act['type'] in ('DEPOSIT', 'WITHDRAWAL') and act['subType'] == 'AFT':
            type_ = 'Direct deposit' if act['type'] == 'DEPOSIT' else 'Pre-authorized debit'
            direction = 'from' if type_ == 'Direct deposit' else 'to'
            institution = act['aftOriginatorName'] if act['aftOriginatorName'] else act['externalCanonicalId']
            act['description'] = f"{type_}: {direction} {institution}"

        elif act['type'] == 'WITHDRAWAL' and act['subType'] == 'BILL_PAY':
            type_ = act['type'].capitalize()
            name = act['billPayPayeeNickname']
            if not name:
                name = act['billPayCompanyName']
            number = act['redactedExternalAccountNumber']
            act['description'] = f"{type_}: Bill pay {name} {number}"

        elif act['type'] == 'P2P_PAYMENT' and act['subType'] in ('SEND', 'SEND_RECEIVED'):
            direction = 'sent to' if act['subType'] == 'SEND' else 'received from'
            p2pHandle = act['p2pHandle']
            act['description'] = f"Cash {direction} {p2pHandle}"

        elif act['type'] == 'PROMOTION' and act['subType'] == 'INCENTIVE_BONUS':
            type_ = act['type'].capitalize()
            subtype = act['subType'].replace('_', ' ').capitalize()
            act['description'] = f"{type_}: {subtype}"

        elif act['type'] == 'REFERRAL' and act['subType'] is None:
            type_ = act['type'].capitalize()
            act['description'] = f"{type_}"

        elif act['type'] == 'CREDIT_CARD' and act['subType'] == 'PURCHASE':
            merchant = act['spendMerchant']
            status = '(Pending) ' if act['status'] == 'authorized' else '' # Posted purchase transactions have status = settled
            act['description'] = f"{status}Credit card purchase: {merchant}"

        elif act['type'] == 'CREDIT_CARD' and act['subType'] == 'HOLD':
            merchant = act['spendMerchant']
            status = '(Pending) ' if act['status'] == 'authorized' else '' # Posted return transactions have subType = REFUND and status = settled
            act['description'] = f"{status}Credit card refund: {merchant}"

        elif act['type'] == 'CREDIT_CARD' and act['subType'] == 'REFUND':
            merchant = act['spendMerchant']
            act['description'] = f"Credit card refund: {merchant}"

        elif act['type'] == 'CREDIT_CARD' and act['subType'] == 'PAYMENT':
            act['description'] = "Credit card payment"

        # TODO: Add other types as needed

    def security_id_to_symbol(self, security_id: str) -> str:
        security_symbol = f"[{security_id}]"
        if self.security_market_data_cache_getter:
            market_data = self.get_security_market_data(security_id)
            if market_data and 'stock' in market_data and market_data['stock']:
                stock = market_data['stock']
                security_symbol = f"{stock['primaryExchange']}:{stock['symbol']}"
        return security_symbol

    def get_etf_details(self, funding_id):
        return self.do_graphql_query(
            'FetchFundsTransfer',
            {'id': funding_id},
            'fundsTransfer',
            'object',
        )

    def get_transfer_details(self, transfer_id):
        return self.do_graphql_query(
            'FetchInstitutionalTransfer',
            {'id': transfer_id},
            'accountTransfer',
            'object',
        )

    def set_security_market_data_cache(self, security_market_data_cache_getter: callable, security_market_data_cache_setter: callable):
        self.security_market_data_cache_getter = security_market_data_cache_getter
        self.security_market_data_cache_setter = security_market_data_cache_setter

    def get_security_market_data(self, security_id: str, use_cache: bool = True):
        if not self.security_market_data_cache_getter or not self.security_market_data_cache_setter:
            use_cache = False

        if use_cache:
            cached_value = self.security_market_data_cache_getter(security_id)
            if cached_value:
                return cached_value

        value = self.do_graphql_query(
            'FetchSecurityMarketData',
            {'id': security_id},
            'security',
            'object',
        )

        if use_cache:
            value = self.security_market_data_cache_setter(security_id, value)

        return value

    def search_security(self, query):
        # Fetch security search results using GraphQL query
        return self.do_graphql_query(
            'FetchSecuritySearchResult',
            {'query': query},
            'securitySearch.results',
            'array',
        )

    def get_security_historical_quotes(self, security_id, time_range='1m'):
        # Fetch historical quotes for a security using GraphQL query
        return self.do_graphql_query(
            'FetchSecurityHistoricalQuotes',
            {
                'id': security_id,
                'timerange': time_range,
            },
            'security.historicalQuotes',
            'array',
        )
