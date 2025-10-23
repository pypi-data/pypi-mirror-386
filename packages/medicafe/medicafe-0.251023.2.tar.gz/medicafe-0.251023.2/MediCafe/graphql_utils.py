# MediLink_GraphQL.py
"""
GraphQL module for United Healthcare Super Connector API
Handles query templates, query building, and response transformations
"""

import json

class GraphQLQueryBuilder:
    """Builder class for constructing GraphQL queries for Super Connector API

    Note on ID card images (idCardImages):
    - Intentionally excluded from all active queries to avoid fetching large
      image payloads and to reduce PHI handling risk in standard flows.
    - If a future feature requires downloading insurance ID cards, add this
      selection to the desired query:
        idCardImages { side content contentType }
      and ensure the implementation does NOT log or persist raw image content.
      Gate any new behavior behind an explicit, opt-in feature flag.
    """
    
    @staticmethod
    def get_eligibility_query():
        """
        Returns the GraphQL query for eligibility checks.
        Uses the exact working format from the successful cURL request.
        """
        return GraphQLQueryBuilder.get_working_eligibility_query()
    
    @staticmethod
    def build_eligibility_variables(
        member_id,
        first_name=None,
        last_name=None,
        date_of_birth=None,
        service_start_date=None,
        service_end_date=None,
        coverage_types=None,
        payer_id=None,
        provider_last_name=None,
        provider_first_name=None,
        provider_npi=None,
        group_number=None,
        trn_id=None,
        service_level_codes=None,
        plan_start_date=None,
        plan_end_date=None,
        family_indicator=None
    ):
        """
        Builds the variables object for the eligibility GraphQL query.
        Uses the exact format that works with the Super Connector API.
        
        Args:
            member_id: Unique identifier for the member
            first_name: First name of the member (not used in working format)
            last_name: Last name of the member (not used in working format)
            date_of_birth: Date of birth in ISO 8601 format (YYYY-MM-DD)
            service_start_date: Start date of the service (not used in working format)
            service_end_date: End date of the service (not used in working format)
            coverage_types: Types of coverage (not used in working format)
            payer_id: Payer identifier
            provider_last_name: Last name of the provider
            provider_first_name: First name of the provider (not used in working format)
            provider_npi: National Provider Identifier (NPI) of the provider
            group_number: Group number (not used in working format)
            trn_id: Transaction identifier (not used in working format)
            service_level_codes: Service level codes (not used in working format)
            plan_start_date: Start date of the plan (not used in working format)
            plan_end_date: End date of the plan (not used in working format)
            family_indicator: Indicator for family/individual (not used in working format)
            
        Returns:
            Dictionary containing the variables for the GraphQL query in working format
        """
        # Build variables in the exact format that works with the API
        variables = {
            "memberId": member_id,
            "firstName": "",  # Always empty string in working format
            "lastName": "",  # Always empty string in working format
            "dateOfBirth": date_of_birth,
            "coverageTypes": [],  # Always empty array in working format
            "payerId": payer_id,
            "providerFirstName": "",  # Always empty string in working format
            "providerLastName": provider_last_name,
            "providerNPI": str(provider_npi) if provider_npi else None,
            # Required empty fields from working format
            "groupNumber": "",
            "serviceLevelCodes": [],
            "planStartDate": "",
            "planEndDate": "",
            "familyIndicator": "",
            "trnId": ""
        }
        
        # Remove None values but keep empty strings and arrays
        variables = {k: v for k, v in variables.items() if v is not None}
        
        return variables
    
    @staticmethod
    def build_eligibility_request(variables):
        """
        Builds the complete GraphQL request body for eligibility checks.
        Uses the working query format.
        
        Args:
            variables: Variables dictionary for the GraphQL query
            
        Returns:
            Complete GraphQL request body
        """
        return GraphQLQueryBuilder.build_working_eligibility_request(variables)

    @staticmethod
    def get_sample_eligibility_request():
        """
        Returns the sample GraphQL request from the swagger documentation.
        This is for testing purposes to verify the endpoint is working.
        """
        return {
            "query": "query Query($input: EligibilityInput!) { checkEligibility(input: $input) { eligibility { eligibilityInfo { trnId member { memberId firstName lastName middleName suffix dateOfBirth gender relationship relationshipCode relationshipTypeCode individualRelationshipCode dependentSequenceNumber } contact { addresses { type street1 street2 city state country zip zip4 } } insuranceInfo { policyNumber eligibilityStartDate eligibilityEndDate planStartDate planEndDate policyStatus planTypeDescription planVariation reportingCode stateOfIssueCode productType productId productCode payerId lineOfBusiness lineOfBusinessCode coverageTypes { typeCode description } } associatedIds { alternateId medicaidRecipientId exchangeMemberId alternateSubscriberId hicNumber mbiNumber subscriberMemberFacingIdentifier survivingSpouseId subscriberId memberReplacementId legacyMemberId customerAccountIdentifier } planLevels { level family { networkStatus planAmount planAmountFrequency remainingAmount } individual { networkStatus planAmount planAmountFrequency remainingAmount } } delegatedInfo { entity payerId contact { phone fax email } addresses { type street1 street2 city state country zip zip4 } } additionalInfo { isReferralRequired } } primaryCarePhysician { isPcpFound lastName firstName middleName phoneNumber address { type street1 street2 city state country zip zip4 } networkStatusCode affiliateHospitalName providerGroupName } coordinationOfBenefit { coordinationOfBenefitDetails { payer { name phoneNumber address { type street1 street2 city state country zip zip4 } } cobPrimacy { indicator description message } } uhgPrimacyStatus { policyEffectiveDate policyTerminationDate primacy { indicator description message } } } idCardImages { side content contentType } providerNetwork { status tier } extendedAttributes { fundingCode fundingType hsa cdhp governmentProgramCode cmsPackageBenefitPlanCode cmsSegmentId cmsContractId marketType obligorId marketSite benefitPlanId virtualVisit planVariation groupNumber legacyPanelNumber coverageLevel sharedArrangement productServiceCode designatedVirtualClinicNetwork medicaidVariableCode healthInsuranceExchangeId memberDiv legalEntityCode } otherBeneficiaries { memberId firstName lastName middleName suffix dateOfBirth gender relationship relationshipCode relationshipTypeCode individualRelationshipCode dependentSequenceNumber } serviceLevels { family { networkStatus services { isVendorOnly service serviceCode serviceDate text status coPayAmount coPayFrequency coInsurancePercent planAmount remainingAmount metYearToDateAmount isReferralObtainedCopay isReferralObtainedCoInsurance referralCopayAmount referralCoInsurancePercent benefitsAllowedFrequencies benefitsRemainingFrequencies message { note { isSingleMessageDetail isViewDetail messages text subMessages { service status copay msg startDate endDate minCopay minCopayMsg maxCopay maxCopayMsg isPrimaryIndicator } limitationInfo { lmtPeriod lmtType lmtOccurPerPeriod lmtDollarPerPeriod message } isMultipleCopaysFound isMultipleCoinsuranceFound } coPay { isSingleMessageDetail isViewDetail messages text subMessages { service status copay msg startDate endDate minCopay minCopayMsg maxCopay maxCopayMsg isPrimaryIndicator } limitationInfo { lmtPeriod lmtType lmtOccurPerPeriod lmtDollarPerPeriod message } isMultipleCopaysFound isMultipleCoinsuranceFound } coInsurance { isSingleMessageDetail isViewDetail messages text subMessages { service status copay msg startDate endDate minCopay minCopayMsg maxCopay maxCopayMsg isPrimaryIndicator } limitationInfo { lmtPeriod lmtType lmtOccurPerPeriod lmtDollarPerPeriod message } isMultipleCopaysFound isMultipleCoinsuranceFound } deductible { isSingleMessageDetail isViewDetail messages text subMessages { service status copay msg startDate endDate minCopay minCopayMsg maxCopay maxCopayMsg isPrimaryIndicator } limitationInfo { lmtPeriod lmtType lmtOccurPerPeriod lmtDollarPerPeriod message } isMultipleCopaysFound isMultipleCoinsuranceFound } benefitsAllowed { isSingleMessageDetail isViewDetail messages text subMessages { service status copay msg startDate endDate minCopay minCopayMsg maxCopay maxCopayMsg isPrimaryIndicator } limitationInfo { lmtPeriod lmtType lmtOccurPerPeriod lmtDollarPerPeriod message } isMultipleCopaysFound isMultipleCoinsuranceFound } benefitsRemaining { isSingleMessageDetail isViewDetail messages text subMessages { service status copay msg startDate endDate minCopay minCopayMsg maxCopay maxCopayMsg isPrimaryIndicator } limitationInfo { lmtPeriod lmtType lmtOccurPerPeriod lmtDollarPerPeriod message } isMultipleCopaysFound isMultipleCoinsuranceFound } coPayList coInsuranceList } } } } } } }",
            "variables": {
                "input": {
                    "memberId": "0001234567",
                    "firstName": "ABC",
                    "lastName": "EFGH",
                    "dateOfBirth": "YYYY-MM-DD",
                    "serviceStartDate": "YYYY-MM-DD",
                    "serviceEndDate": "YYYY-MM-DD",
                    "coverageTypes": [
                        "Medical"
                    ],
                    "payerId": "12345",
                    "providerLastName": "XYZ",
                    "providerFirstName": "QWERT",
                    "providerNPI": "1234567890",
                    "groupNumber": "",
                    "serviceLevelCodes": [],
                    "planStartDate": "",
                    "planEndDate": "",
                    "familyIndicator": "",
                    "trnId": ""
                }
            }
        }

    @staticmethod
    def get_working_eligibility_query():
        """
        Returns the exact GraphQL query format that works with the Super Connector API.
        This matches the exact format from the successful cURL request.
        """
        return """query Query($input: EligibilityInput!) {\r\n \r\n  checkEligibility(input: $input) {\r\n    eligibility {\r\n      eligibilityInfo {\r\n        trnId\r\n        member {\r\n          memberId\r\n          firstName\r\n          lastName\r\n          middleName\r\n          suffix\r\n          dateOfBirth\r\n          gender\r\n          relationship\r\n          relationshipCode\r\n          relationshipTypeCode\r\n          individualRelationshipCode\r\n          dependentSequenceNumber\r\n        }\r\n        contact {\r\n          addresses {\r\n            type\r\n            street1\r\n            street2\r\n            city\r\n            state\r\n            country\r\n            zip\r\n            zip4\r\n          }\r\n        }\r\n        insuranceInfo {\r\n          policyNumber\r\n          eligibilityStartDate\r\n          eligibilityEndDate\r\n          planStartDate\r\n          planEndDate\r\n          policyStatus\r\n          planTypeDescription\r\n          planVariation\r\n          reportingCode\r\n          stateOfIssueCode\r\n          productType\r\n          productId\r\n          productCode\r\n          payerId\r\n          lineOfBusiness\r\n          lineOfBusinessCode\r\n          coverageTypes {\r\n            typeCode\r\n            description\r\n          }\r\n        }\r\n        associatedIds {\r\n          alternateId\r\n          medicaidRecipientId\r\n          exchangeMemberId\r\n          alternateSubscriberId\r\n          hicNumber\r\n          mbiNumber\r\n          subscriberMemberFacingIdentifier\r\n          survivingSpouseId\r\n          subscriberId\r\n          memberReplacementId\r\n          legacyMemberId\r\n          customerAccountIdentifier\r\n        }\r\n        planLevels {\r\n          level\r\n          family {\r\n            networkStatus\r\n            planAmount\r\n            planAmountFrequency\r\n            remainingAmount\r\n          }\r\n          individual {\r\n            networkStatus\r\n            planAmount\r\n            planAmountFrequency\r\n            remainingAmount\r\n          }\r\n        }\r\n        delegatedInfo {\r\n          entity\r\n          payerId\r\n          contact {\r\n            phone\r\n            fax\r\n            email\r\n          }\r\n          addresses {\r\n            type\r\n            street1\r\n            street2\r\n            city\r\n            state\r\n            country\r\n            zip\r\n            zip4\r\n          }\r\n        }\r\n        additionalInfo {\r\n          isReferralRequired\r\n        }\r\n      }\r\n      primaryCarePhysician {\r\n        isPcpFound\r\n        lastName\r\n        firstName\r\n        middleName\r\n        phoneNumber\r\n        address {\r\n          type\r\n          street1\r\n          street2\r\n          city\r\n          state\r\n          country\r\n          zip\r\n          zip4\r\n        }\r\n        networkStatusCode\r\n        affiliateHospitalName\r\n        providerGroupName\r\n      }\r\n      coordinationOfBenefit {\r\n        coordinationOfBenefitDetails {\r\n          payer {\r\n            name\r\n            phoneNumber\r\n            address {\r\n              type\r\n              street1\r\n              street2\r\n              city\r\n              state\r\n              country\r\n              zip\r\n              zip4\r\n            }\r\n          }\r\n          cobPrimacy {\r\n            indicator\r\n            description\r\n            message\r\n          }\r\n        }\r\n        uhgPrimacyStatus {\r\n          policyEffectiveDate\r\n          policyTerminationDate\r\n          primacy {\r\n            indicator\r\n            description\r\n            message\r\n          }\r\n        }\r\n      }\r\n      providerNetwork {\r\n        status\r\n        tier\r\n      }\r\n      extendedAttributes {\r\n        fundingCode\r\n        fundingType\r\n        hsa\r\n        cdhp\r\n        governmentProgramCode\r\n        cmsPackageBenefitPlanCode\r\n        cmsSegmentId\r\n        cmsContractId\r\n        marketType\r\n        obligorId\r\n        marketSite\r\n        benefitPlanId\r\n        virtualVisit\r\n        planVariation\r\n        groupNumber\r\n        legacyPanelNumber\r\n        coverageLevel\r\n        sharedArrangement\r\n        productServiceCode\r\n        designatedVirtualClinicNetwork\r\n        medicaidVariableCode\r\n        healthInsuranceExchangeId\r\n        memberDiv\r\n        legalEntityCode\r\n      }\r\n      otherBeneficiaries {\r\n        memberId\r\n        firstName\r\n        lastName\r\n        middleName\r\n        suffix\r\n        dateOfBirth\r\n        gender\r\n        relationship\r\n        relationshipCode\r\n        relationshipTypeCode\r\n        individualRelationshipCode\r\n        dependentSequenceNumber\r\n      }\r\n      serviceLevels {\r\n        family {\r\n          networkStatus\r\n          services {\r\n            isVendorOnly\r\n            service\r\n            serviceCode\r\n            serviceDate\r\n            text\r\n            status\r\n            coPayAmount\r\n            coPayFrequency\r\n            coInsurancePercent\r\n            planAmount\r\n            remainingAmount\r\n            metYearToDateAmount\r\n            isReferralObtainedCopay\r\n            isReferralObtainedCoInsurance\r\n            referralCopayAmount\r\n            referralCoInsurancePercent\r\n            benefitsAllowedFrequencies\r\n            benefitsRemainingFrequencies\r\n            message {\r\n              note {\r\n                isSingleMessageDetail\r\n                isViewDetail\r\n                messages\r\n                text\r\n                subMessages {\r\n                  service\r\n                  status\r\n                  copay\r\n                  msg\r\n                  startDate\r\n                  endDate\r\n                  minCopay\r\n                  minCopayMsg\r\n                  maxCopay\r\n                  maxCopayMsg\r\n                  isPrimaryIndicator\r\n                }\r\n                limitationInfo {\r\n                  lmtPeriod\r\n                  lmtType\r\n                  lmtOccurPerPeriod\r\n                  lmtDollarPerPeriod\r\n                  message\r\n                }\r\n                isMultipleCopaysFound\r\n                isMultipleCoinsuranceFound\r\n              }\r\n              coPay {\r\n                isSingleMessageDetail\r\n                isViewDetail\r\n                messages\r\n                text\r\n                subMessages {\r\n                  service\r\n                  status\r\n                  copay\r\n                  msg\r\n                  startDate\r\n                  endDate\r\n                  minCopay\r\n                  minCopayMsg\r\n                  maxCopay\r\n                  maxCopayMsg\r\n                  isPrimaryIndicator\r\n                }\r\n                limitationInfo {\r\n                  lmtPeriod\r\n                  lmtType\r\n                  lmtOccurPerPeriod\r\n                  lmtDollarPerPeriod\r\n                  message\r\n                }\r\n                isMultipleCopaysFound\r\n                isMultipleCoinsuranceFound\r\n              }\r\n              coInsurance {\r\n                isSingleMessageDetail\r\n                isViewDetail\r\n                messages\r\n                text\r\n                subMessages {\r\n                  service\r\n                  status\r\n                  copay\r\n                  msg\r\n                  startDate\r\n                  endDate\r\n                  minCopay\r\n                  minCopayMsg\r\n                  maxCopay\r\n                  maxCopayMsg\r\n                  isPrimaryIndicator\r\n                }\r\n                limitationInfo {\r\n                  lmtPeriod\r\n                  lmtType\r\n                  lmtOccurPerPeriod\r\n                  lmtDollarPerPeriod\r\n                  message\r\n                }\r\n                isMultipleCopaysFound\r\n                isMultipleCoinsuranceFound\r\n              }\r\n              deductible {\r\n                isSingleMessageDetail\r\n                isViewDetail\r\n                messages\r\n                text\r\n                subMessages {\r\n                  service\r\n                  status\r\n                  copay\r\n                  msg\r\n                  startDate\r\n                  endDate\r\n                  minCopay\r\n                  minCopayMsg\r\n                  maxCopay\r\n                  maxCopayMsg\r\n                  isPrimaryIndicator\r\n                }\r\n                limitationInfo {\r\n                  lmtPeriod\r\n                  lmtType\r\n                  lmtOccurPerPeriod\r\n                  lmtDollarPerPeriod\r\n                  message\r\n                }\r\n                isMultipleCopaysFound\r\n                isMultipleCoinsuranceFound\r\n              }\r\n              benefitsAllowed {\r\n                isSingleMessageDetail\r\n                isViewDetail\r\n                messages\r\n                text\r\n                subMessages {\r\n                  service\r\n                  status\r\n                  copay\r\n                  msg\r\n                  startDate\r\n                  endDate\r\n                  minCopay\r\n                  minCopayMsg\r\n                  maxCopay\r\n                  maxCopayMsg\r\n                  isPrimaryIndicator\r\n                }\r\n                limitationInfo {\r\n                  lmtPeriod\r\n                  lmtType\r\n                  lmtOccurPerPeriod\r\n                  lmtDollarPerPeriod\r\n                  message\r\n                }\r\n                isMultipleCopaysFound\r\n                isMultipleCoinsuranceFound\r\n              }\r\n              benefitsRemaining {\r\n                isSingleMessageDetail\r\n                isViewDetail\r\n                messages\r\n                text\r\n                subMessages {\r\n                  service\r\n                  status\r\n                  copay\r\n                  msg\r\n                  startDate\r\n                  endDate\r\n                  minCopay\r\n                  minCopayMsg\r\n                  maxCopay\r\n                  maxCopayMsg\r\n                  isPrimaryIndicator\r\n                }\r\n                limitationInfo {\r\n                  lmtPeriod\r\n                  lmtType\r\n                  lmtOccurPerPeriod\r\n                  lmtDollarPerPeriod\r\n                  message\r\n                }\r\n                isMultipleCopaysFound\r\n                isMultipleCoinsuranceFound\r\n              }\r\n              coPayList\r\n              coInsuranceList\r\n            }\r\n          }\r\n        }\r\n      }\r\n    }\r\n  }\r\n}"""

    @staticmethod
    def build_working_eligibility_request(variables):
        """
        Builds the complete GraphQL request body using the working query format.
        
        Args:
            variables: Variables dictionary for the GraphQL query
            
        Returns:
            Complete GraphQL request body with working query format
        """
        return {
            "query": GraphQLQueryBuilder.get_working_eligibility_query(),
            "variables": {
                "input": variables
            }
        }

    # ------------------------------------------------------------------
    # OPTUMAI compatibility: minimal query that avoids fields not present
    # ------------------------------------------------------------------
    @staticmethod
    def get_optumai_minimal_query():
        """
        Returns a minimal GraphQL query for OPTUMAI endpoint that avoids
        fields reported as undefined by the schema.
        """
        return """query Query($input: EligibilityInput!) {\r\n  checkEligibility(input: $input) {\r\n    eligibility {\r\n      eligibilityInfo {\r\n        trnId\r\n        member {\r\n          memberId\r\n          firstName\r\n          lastName\r\n          middleName\r\n          dateOfBirth\r\n          gender\r\n          relationshipCode\r\n          dependentSequenceNumber\r\n          individualRelationship { code description }\r\n          relationshipType { code description }\r\n        }\r\n        insuranceInfo {\r\n          policyStatus\r\n          planTypeDescription\r\n          payerId\r\n        }\r\n        planLevels { level }\r\n      }\r\n    }\r\n  }\r\n}"""

    @staticmethod
    def build_optumai_minimal_request(variables):
        """
        Builds the minimal GraphQL request body for OPTUMAI.
        """
        return {
            "query": GraphQLQueryBuilder.get_optumai_minimal_query(),
            "variables": {
                "input": variables
            }
        }

    # ------------------------------------------------------------------
    # OPTUMAI compatibility: enriched query with commonly used fields
    # ------------------------------------------------------------------
    @staticmethod
    def get_optumai_enriched_query():
        """
        Returns an enriched GraphQL query for OPTUMAI that includes
        eligibilityInfo core fields plus planLevels details that our
        downstream logic commonly uses. Avoids legacy-only fields.
        """
        return """query Query($input: EligibilityInput!) {\r\n  checkEligibility(input: $input) {\r\n    eligibility {\r\n      eligibilityInfo {\r\n        trnId\r\n        member {\r\n          memberId\r\n          firstName\r\n          lastName\r\n          middleName\r\n          dateOfBirth\r\n          gender\r\n          relationshipCode\r\n          dependentSequenceNumber\r\n          individualRelationship { code description }\r\n          relationshipType { code description }\r\n        }\r\n        insuranceInfo {\r\n          policyNumber\r\n          eligibilityStartDate\r\n          eligibilityEndDate\r\n          planStartDate\r\n          planEndDate\r\n          policyStatus\r\n          planTypeDescription\r\n          payerId\r\n          lineOfBusinessCode\r\n          coverageType\r\n          insuranceTypeCode\r\n          insuranceType\r\n          stateOfIssueCode\r\n          productType\r\n          productId\r\n          productCode\r\n        }\r\n        associatedIds {\r\n          alternateId\r\n          medicaidRecipientId\r\n          exchangeMemberId\r\n          alternateSubscriberId\r\n          hicNumber\r\n          mbiNumber\r\n          subscriberMemberFacingIdentifier\r\n          survivingSpouseId\r\n          subscriberId\r\n          memberReplacementId\r\n          legacyMemberId\r\n          healthInsuranceExchangeId\r\n        }\r\n        planLevels {\r\n          level\r\n          family {\r\n            networkStatus\r\n            planAmount\r\n            planAmountFrequency\r\n            remainingAmount\r\n          }\r\n          individual {\r\n            networkStatus\r\n            planAmount\r\n            planAmountFrequency\r\n            remainingAmount\r\n          }\r\n        }\r\n      }\r\n      providerNetwork { status tier }\r\n    }\r\n  }\r\n}"""

    @staticmethod
    def build_optumai_enriched_request(variables):
        """
        Builds the enriched GraphQL request body for OPTUMAI.
        """
        return {
            "query": GraphQLQueryBuilder.get_optumai_enriched_query(),
            "variables": {
                "input": variables
            }
        }

    # ------------------------------------------------------------------
    # OPTUMAI Claims Inquiry (Real Claim Inquiry) - minimal searchClaim
    # ------------------------------------------------------------------
    @staticmethod
    def get_optumai_claims_inquiry_query():
        """
        Returns a minimal GraphQL query for searchClaim that includes fields
        necessary to map into the existing legacy claims summary structure
        (memberInfo, claimSummary, crosswalk data).
        """
        return (
            "query searchClaim($searchClaimInput: SearchClaimInput!) {\n"
            "  searchClaimResponse(input: $searchClaimInput) {\n"
            "    claims {\n"
            "      claimNumber\n"
            "      claimStatus\n"
            "      member { firstName lastName }\n"
            "      claimEvents { processedDate serviceStartDate }\n"
            "      claimLevelTotalAmount {\n"
            "        totalBilledChargeAmount\n"
            "        totalAllowedAmount\n"
            "        totalPaidAmount\n"
            "        totalPatientResponsibilityAmount\n"
            "      }\n"
            "      claimStatusCrosswalkData {\n"
            "        claim507Code claim507CodeDesc claim508Code claim508CodeDesc adjudicatedClaimSuffixCode\n"
            "      }\n"
            "    }\n"
            "    pagination { hasMoreRecords nextPageToken }\n"
            "  }\n"
            "}"
        )

    @staticmethod
    def build_optumai_claims_inquiry_request(search_claim_input):
        """
        Build the GraphQL request body for searchClaim.

        Args:
            search_claim_input: dict with keys matching SearchClaimInput (e.g.,
              payerId (required), serviceStartDate, serviceEndDate, claimNumber, etc.)
        """
        return {
            "query": GraphQLQueryBuilder.get_optumai_claims_inquiry_query(),
            "operationName": "searchClaim",
            "variables": {
                "searchClaimInput": search_claim_input or {}
            }
        }

def _map_graphql_error_to_status_message(error):
    """Map provider GraphQL error to (statuscode, message) using simple heuristics.
    Python 3.4-compatible; avoids dependencies and centralizes logic.
    """
    try:
        if not isinstance(error, dict):
            return '500', 'GraphQL error: unknown format'
        code = ((error.get('extensions', {}) or {}).get('code') or
                error.get('code') or 'GRAPHQL_ERROR')
        msg = (error.get('message') or error.get('description') or 'GraphQL error')
        code_upper = str(code).upper()
        msg_lower = str(msg).lower()

        # 401 auth failures
        if (code == 'UNAUTHORIZED_AUTHENTICATION_FAILED' or
                ('UNAUTH' in code_upper) or
                ('AUTHENTICATION' in code_upper)):
            return '401', 'Authentication failed: {}'.format(msg)

        # 403 authorization/access issues
        if ('FORBIDDEN' in code_upper) or ('AUTHORIZATION' in code_upper) or ('ACCESS_DENIED' in code_upper) or \
           ('forbidden' in msg_lower) or ('permission' in msg_lower):
            return '403', 'Authorization failed: {}'.format(msg)

        # Default
        return '500', '{}: {}'.format(code, msg)
    except Exception:
        return '500', 'GraphQL error: unknown'


class GraphQLResponseTransformer:
    """Transforms GraphQL responses to match REST API format"""
    
    @staticmethod
    def transform_eligibility_response(graphql_response):
        """
        Transforms the GraphQL eligibility response to match the REST API format.
        This ensures the calling code receives the same structure regardless of endpoint.
        
        Args:
            graphql_response: Raw GraphQL response from Super Connector API
            
        Returns:
            Transformed response matching REST API format
        """
        try:
            # Check for authentication/authorization errors first
            if 'errors' in graphql_response:
                error = graphql_response['errors'][0]
                statuscode, mapped_msg = _map_graphql_error_to_status_message(error)
                return {
                    'statuscode': statuscode,
                    'message': mapped_msg,
                    'rawGraphQLResponse': graphql_response
                }
            
            # Check if GraphQL response has data
            if 'data' not in graphql_response:
                return {
                    'statuscode': '404',
                    'message': 'No data found in GraphQL response',
                    'rawGraphQLResponse': graphql_response
                }
            
            if 'checkEligibility' not in graphql_response['data']:
                return {
                    'statuscode': '404',
                    'message': 'No eligibility data found in GraphQL response',
                    'rawGraphQLResponse': graphql_response
                }
            
            # Handle case where checkEligibility is null (authentication failure)
            if graphql_response['data']['checkEligibility'] is None:
                return {
                    'statuscode': '401',
                    'message': 'Authentication failed - checkEligibility returned null',
                    'rawGraphQLResponse': graphql_response
                }
            
            eligibility_data = graphql_response['data']['checkEligibility']['eligibility']
            if not eligibility_data:
                return {
                    'statuscode': '404',
                    'message': 'No eligibility records found',
                    'rawGraphQLResponse': graphql_response
                }
            
            # Take the first eligibility record (assuming single member query)
            first_eligibility = eligibility_data[0]
            eligibility_info = first_eligibility.get('eligibilityInfo', {})
            
            # Transform to REST-like format
            rest_response = {
                'statuscode': '200',
                'message': 'Eligibility found',
                'rawGraphQLResponse': graphql_response  # Include original response for debugging
            }
            
            # Safely extract member information
            member_info = eligibility_info.get('member', {})
            if member_info:
                rest_response.update({
                    'memberId': member_info.get('memberId'),
                    'firstName': member_info.get('firstName'),
                    'lastName': member_info.get('lastName'),
                    'middleName': member_info.get('middleName'),
                    'suffix': member_info.get('suffix'),
                    'dateOfBirth': member_info.get('dateOfBirth'),
                    'gender': member_info.get('gender'),
                    'relationship': member_info.get('relationship'),
                    'relationshipCode': member_info.get('relationshipCode'),
                    'individualRelationshipCode': member_info.get('individualRelationshipCode'),
                    'dependentSequenceNumber': member_info.get('dependentSequenceNumber')
                })
            
            # Safely extract insurance information
            insurance_info = eligibility_info.get('insuranceInfo', {})
            if insurance_info:
                rest_response.update({
                    'policyNumber': insurance_info.get('policyNumber'),
                    'eligibilityStartDate': insurance_info.get('eligibilityStartDate'),
                    'eligibilityEndDate': insurance_info.get('eligibilityEndDate'),
                    'planStartDate': insurance_info.get('planStartDate'),
                    'planEndDate': insurance_info.get('planEndDate'),
                    'policyStatus': insurance_info.get('policyStatus'),
                    'planTypeDescription': insurance_info.get('planTypeDescription'),
                    'planVariation': insurance_info.get('planVariation'),
                    'reportingCode': insurance_info.get('reportingCode'),
                    'stateOfIssueCode': insurance_info.get('stateOfIssueCode'),
                    'productType': insurance_info.get('productType'),
                    'productId': insurance_info.get('productId'),
                    'productCode': insurance_info.get('productCode'),
                    'lineOfBusiness': insurance_info.get('lineOfBusiness'),
                    'lineOfBusinessCode': insurance_info.get('lineOfBusinessCode'),
                    'coverageTypes': insurance_info.get('coverageTypes', []),
                    # Expose insurance type fields for downstream logic/UI
                    'insuranceTypeCode': insurance_info.get('insuranceTypeCode'),
                    'insuranceType': insurance_info.get('insuranceType')
                })
            
            # Safely extract associated IDs
            associated_ids = eligibility_info.get('associatedIds', {})
            if associated_ids:
                rest_response.update({
                    'alternateId': associated_ids.get('alternateId'),
                    'medicaidRecipientId': associated_ids.get('medicaidRecipientId'),
                    'exchangeMemberId': associated_ids.get('exchangeMemberId'),
                    'alternateSubscriberId': associated_ids.get('alternateSubscriberId'),
                    'hicNumber': associated_ids.get('hicNumber'),
                    'mbiNumber': associated_ids.get('mbiNumber'),
                    'subscriberMemberFacingIdentifier': associated_ids.get('subscriberMemberFacingIdentifier'),
                    'survivingSpouseId': associated_ids.get('survivingSpouseId'),
                    'subscriberId': associated_ids.get('subscriberId'),
                    'memberReplacementId': associated_ids.get('memberReplacementId'),
                    'legacyMemberId': associated_ids.get('legacyMemberId'),
                    'customerAccountIdentifier': associated_ids.get('customerAccountIdentifier')
                })
            
            # Safely extract plan levels
            plan_levels = eligibility_info.get('planLevels', [])
            if plan_levels:
                rest_response['planLevels'] = plan_levels
            
            # Safely extract delegated info
            delegated_info = eligibility_info.get('delegatedInfo', [])
            if delegated_info:
                rest_response['delegatedInfo'] = delegated_info
            
            # Safely extract additional information
            additional_info = eligibility_info.get('additionalInfo', {})
            if additional_info:
                rest_response['isReferralRequired'] = additional_info.get('isReferralRequired')
            
            # Safely extract primary care physician
            pcp = first_eligibility.get('primaryCarePhysician', {})
            if pcp:
                rest_response.update({
                    'pcpIsFound': pcp.get('isPcpFound'),
                    'pcpLastName': pcp.get('lastName'),
                    'pcpFirstName': pcp.get('firstName'),
                    'pcpMiddleName': pcp.get('middleName'),
                    'pcpPhoneNumber': pcp.get('phoneNumber'),
                    'pcpAddress': pcp.get('address'),
                    'pcpNetworkStatusCode': pcp.get('networkStatusCode'),
                    'pcpAffiliateHospitalName': pcp.get('affiliateHospitalName'),
                    'pcpProviderGroupName': pcp.get('providerGroupName')
                })
            
            # Safely extract coordination of benefit
            cob = first_eligibility.get('coordinationOfBenefit', {})
            if cob:
                # Transform COB to handle missing 'id' field in payer
                transformed_cob = cob.copy()
                if 'coordinationOfBenefitDetails' in transformed_cob:
                    for detail in transformed_cob['coordinationOfBenefitDetails']:
                        if 'payer' in detail and 'id' not in detail['payer']:
                            # Add empty id field for compatibility
                            detail['payer']['id'] = None
                rest_response['coordinationOfBenefit'] = transformed_cob
            
            # Safely extract ID card images
            id_card_images = first_eligibility.get('idCardImages', [])
            if id_card_images:
                rest_response['idCardImages'] = id_card_images
            
            # Safely extract provider network information
            provider_network = first_eligibility.get('providerNetwork', {})
            if provider_network:
                rest_response.update({
                    'networkStatus': provider_network.get('status'),
                    'networkTier': provider_network.get('tier')
                })
            
            # Safely extract service levels
            service_levels = first_eligibility.get('serviceLevels', [])
            if service_levels:
                rest_response['serviceLevels'] = service_levels
                
                # Extract first service as example for compatibility
                if service_levels and len(service_levels) > 0:
                    first_service_level = service_levels[0]
                    individual_services = first_service_level.get('individual', [])
                    if individual_services and len(individual_services) > 0:
                        first_individual = individual_services[0]
                        services = first_individual.get('services', [])
                        if services and len(services) > 0:
                            first_service = services[0]
                            rest_response.update({
                                'serviceCode': first_service.get('serviceCode'),
                                'serviceText': first_service.get('text'),
                                'serviceStatus': first_service.get('status'),
                                'coPayAmount': first_service.get('coPayAmount'),
                                'coPayFrequency': first_service.get('coPayFrequency'),
                                'coInsurancePercent': first_service.get('coInsurancePercent'),
                                'planAmount': first_service.get('planAmount'),
                                'remainingAmount': first_service.get('remainingAmount'),
                                'metYearToDateAmount': first_service.get('metYearToDateAmount')
                            })
            
            # Safely extract extended attributes
            extended_attrs = first_eligibility.get('extendedAttributes', {})
            if extended_attrs:
                rest_response.update({
                    'fundingCode': extended_attrs.get('fundingCode'),
                    'fundingType': extended_attrs.get('fundingType'),
                    'hsa': extended_attrs.get('hsa'),
                    'cdhp': extended_attrs.get('cdhp'),
                    'governmentProgramCode': extended_attrs.get('governmentProgramCode'),
                    'cmsPackageBenefitPlanCode': extended_attrs.get('cmsPackageBenefitPlanCode'),
                    'cmsSegmentId': extended_attrs.get('cmsSegmentId'),
                    'cmsContractId': extended_attrs.get('cmsContractId'),
                    'marketType': extended_attrs.get('marketType'),
                    'obligorId': extended_attrs.get('obligorId'),
                    'marketSite': extended_attrs.get('marketSite'),
                    'benefitPlanId': extended_attrs.get('benefitPlanId'),
                    'virtualVisit': extended_attrs.get('virtualVisit'),
                    'planVariation': extended_attrs.get('planVariation'),
                    'groupNumber': extended_attrs.get('groupNumber'),
                    'legacyPanelNumber': extended_attrs.get('legacyPanelNumber'),
                    'coverageLevel': extended_attrs.get('coverageLevel'),
                    'sharedArrangement': extended_attrs.get('sharedArrangement'),
                    'productServiceCode': extended_attrs.get('productServiceCode'),
                    'designatedVirtualClinicNetwork': extended_attrs.get('designatedVirtualClinicNetwork'),
                    'medicaidVariableCode': extended_attrs.get('medicaidVariableCode'),
                    'healthInsuranceExchangeId': extended_attrs.get('healthInsuranceExchangeId'),
                    'memberDiv': extended_attrs.get('memberDiv'),
                    'legalEntityCode': extended_attrs.get('legalEntityCode')
                })
            
            # Safely extract other beneficiaries
            other_beneficiaries = first_eligibility.get('otherBeneficiaries', [])
            if other_beneficiaries:
                rest_response['otherBeneficiaries'] = other_beneficiaries
            
            return rest_response
            
        except Exception as e:
            # Log the error and the response structure for debugging
            print("Error transforming GraphQL response: {}".format(str(e)))
            print("Response structure: {}".format(json.dumps(graphql_response, indent=2)))
            return {
                'statuscode': '500',
                'message': 'Error processing GraphQL response: {}'.format(str(e)),
                'rawGraphQLResponse': graphql_response
            }

    @staticmethod
    def transform_claims_inquiry_response_to_legacy(graphql_response):
        """
        Transform OPTUMAI searchClaim GraphQL response into the legacy
        claims summary format expected by downstream code (e.g.,
        MediLink_ClaimStatus.extract_claim_data).
        """
        try:
            # Handle GraphQL errors
            if isinstance(graphql_response, dict) and 'errors' in graphql_response:
                first_err = graphql_response['errors'][0] if graphql_response['errors'] else {}
                statuscode, mapped_msg = _map_graphql_error_to_status_message(first_err)
                return {
                    'statuscode': statuscode,
                    'message': mapped_msg,
                    'rawGraphQLResponse': graphql_response
                }

            data = (graphql_response or {}).get('data') or {}
            search_resp = data.get('searchClaimResponse') or {}
            claims = search_resp.get('claims') or []
            pagination = search_resp.get('pagination') or {}

            legacy_claims = []
            for c in claims:
                member = c.get('member') or {}
                events = c.get('claimEvents') or {}
                totals = c.get('claimLevelTotalAmount') or {}
                xwalk_list = c.get('claimStatusCrosswalkData') or []

                # Map crosswalk to legacy keys list
                legacy_xwalk = []
                for x in xwalk_list:
                    legacy_xwalk.append({
                        'clm507Cd': x.get('claim507Code'),
                        'clm507CdDesc': x.get('claim507CodeDesc'),
                        'clm508Cd': x.get('claim508Code'),
                        'clm508CdDesc': x.get('claim508CodeDesc'),
                        'clmIcnSufxCd': x.get('adjudicatedClaimSuffixCode')
                    })

                legacy_claims.append({
                    'claimNumber': c.get('claimNumber'),
                    'claimStatus': c.get('claimStatus'),
                    'memberInfo': {
                        'ptntFn': member.get('firstName'),
                        'ptntLn': member.get('lastName')
                    },
                    'claimSummary': {
                        'processedDt': events.get('processedDate') or '',
                        'firstSrvcDt': events.get('serviceStartDate') or '',
                        'totalChargedAmt': (totals.get('totalBilledChargeAmount') or ''),
                        'totalAllowdAmt': (totals.get('totalAllowedAmount') or ''),
                        'totalPaidAmt': (totals.get('totalPaidAmount') or ''),
                        'totalPtntRespAmt': (totals.get('totalPatientResponsibilityAmount') or ''),
                        'clmXWalkData': legacy_xwalk
                    }
                })

            next_token = pagination.get('nextPageToken')
            has_more = bool(pagination.get('hasMoreRecords'))

            transformed = {
                'statuscode': '200',
                'message': 'Claims found' if legacy_claims else 'No claims found',
                'claims': legacy_claims,
                # Maintain legacy pagination signaling by mapping to 'transactionId'
                'transactionId': next_token if has_more else None,
                'rawGraphQLResponse': graphql_response
            }
            return transformed
        except Exception as e:
            print("Error transforming Claims Inquiry response: {}".format(str(e)))
            return {
                'statuscode': '500',
                'message': 'Error processing Claims Inquiry response: {}'.format(str(e)),
                'rawGraphQLResponse': graphql_response
            }

# Convenience functions for easy access

def get_eligibility_query():
    """Get the eligibility GraphQL query (working format)"""
    return GraphQLQueryBuilder.get_eligibility_query()

def build_eligibility_variables(**kwargs):
    """Build eligibility query variables in working format"""
    return GraphQLQueryBuilder.build_eligibility_variables(**kwargs)

def build_eligibility_request(variables):
    """Build complete GraphQL request body with working format"""
    return GraphQLQueryBuilder.build_eligibility_request(variables)

def build_optumai_minimal_request(variables):
    """Build minimal GraphQL request body for OPTUMAI"""
    return GraphQLQueryBuilder.build_optumai_minimal_request(variables)

def build_optumai_enriched_request(variables):
    """Build enriched GraphQL request body for OPTUMAI"""
    return GraphQLQueryBuilder.build_optumai_enriched_request(variables)

def build_optumai_claims_inquiry_request(search_claim_input):
    """Build GraphQL request body for OPTUMAI searchClaim"""
    return GraphQLQueryBuilder.build_optumai_claims_inquiry_request(search_claim_input)

def transform_eligibility_response(graphql_response):
    """Transform GraphQL eligibility response to REST format"""
    return GraphQLResponseTransformer.transform_eligibility_response(graphql_response)

def transform_claims_inquiry_response_to_legacy(graphql_response):
    """Transform OPTUMAI searchClaim response to legacy claims summary format"""
    return GraphQLResponseTransformer.transform_claims_inquiry_response_to_legacy(graphql_response)

def get_sample_eligibility_request():
    """Get the sample GraphQL request from swagger documentation"""
    return GraphQLQueryBuilder.get_sample_eligibility_request()

# -----------------------------------------------------------------------------
# Phase 2 scaffolding: centralized direct SBR09 extraction (placeholder)
# -----------------------------------------------------------------------------

# Placeholder path for future API-provided SBR09 value.
# Accepts either a top-level key (e.g., 'sbr09Code') or a dotted path
# (e.g., 'eligibilityInfo.insuranceInfo.sbr09'). Update when contract is finalized.
FUTURE_SBR09_FIELD_PATH = '<INSERT_SBR09_FIELD_PATH>'


def _get_nested_value(data, dotted_path):
    """Safely get nested value from dict given a dotted path."""
    try:
        current = data
        for part in dotted_path.split('.'):
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        return current
    except Exception:
        return None


def _is_valid_sbr09(code):
    if not isinstance(code, str):
        return False
    c = code.strip().upper()
    return 1 <= len(c) <= 3 and c.isalnum()


def _normalize_sbr09(code):
    return str(code).strip().upper()


def extract_sbr09_direct(response_dict):
    """
    Extract SBR09 directly from a transformed GraphQL response or raw GraphQL if the
    provider API supplies it. Returns None until FUTURE_SBR09_FIELD_PATH is set and value is present.

    - No mapping is performed. Only format checks are applied.
    - Accepts either top-level key or dotted path.
    """
    if not FUTURE_SBR09_FIELD_PATH or FUTURE_SBR09_FIELD_PATH.startswith('<'):
        return None

    # Try top-level lookup
    raw_value = response_dict.get(FUTURE_SBR09_FIELD_PATH)

    # If not found, try dotted path
    if raw_value is None and '.' in FUTURE_SBR09_FIELD_PATH:
        raw_value = _get_nested_value(response_dict, FUTURE_SBR09_FIELD_PATH)

    if raw_value is None:
        return None

    candidate = _normalize_sbr09(raw_value)
    return candidate if _is_valid_sbr09(candidate) else None 