"""
Adapter Module

Converts GooglePatentData to USPTO data model structures that are compatible
with the existing USPatent and USPublication classes.
"""

from typing import Optional
from dataclasses import dataclass

from uspto_data.data_model import (
    PatentFileWrapperDataBag,
    ApplicationMetaData,
    InventorBag,
    CorrespondenceAddressBag,
    EntityStatusData,
    EventDataBag,
    PgPubDocumentMetaData,
    GrantDocumentMetaData
)
from uspto_data.google_patents.scraper import GooglePatentData


class GooglePatentsAdapter:
    """
    Adapts scraped Google Patents data to USPTO API data model structures.

    Creates mock USPTO API response objects that are compatible with
    existing USPatent and USPublication entity classes.
    """

    @staticmethod
    def create_patent_file_wrapper_data_bag(google_data: GooglePatentData) -> PatentFileWrapperDataBag:
        """
        Create a PatentFileWrapperDataBag from Google Patents data.

        :param google_data: Scraped Google Patents data
        :return: PatentFileWrapperDataBag compatible with existing entity classes
        """
        # Create application metadata
        application_metadata = GooglePatentsAdapter._create_application_metadata(google_data)

        # Create inventor bag
        inventor_bag = GooglePatentsAdapter._create_inventor_bag(google_data)

        # Create event data bag
        event_data_bag = GooglePatentsAdapter._create_event_data_bag(google_data)

        # Create document metadata
        pgpub_metadata = GooglePatentsAdapter._create_pgpub_metadata(google_data)
        grant_metadata = GooglePatentsAdapter._create_grant_metadata(google_data)

        # Construct the patent file wrapper data bag
        patent_info = PatentFileWrapperDataBag(
            applicationNumberText=google_data.application_number,
            applicationMetaData=application_metadata,
            correspondenceAddressBag=[],
            assignmentBag=[],
            recordAttorney=None,
            foreignPriorityBag=[],
            parentContinuityBag=[],
            childContinuityBag=[],
            patentTermAdjustmentData=None,
            eventDataBag=event_data_bag,
            pgpubDocumentMetaData=pgpub_metadata,
            grantDocumentMetaData=grant_metadata,
            lastIngestionTime=None
        )

        return patent_info

    @staticmethod
    def _create_application_metadata(google_data: GooglePatentData) -> ApplicationMetaData:
        """Create ApplicationMetaData from Google Patents data."""
        return ApplicationMetaData(
            nationalStageIndicator=None,
            entityStatusData=EntityStatusData(
                smallEntityStatusIndicator=None,
                businessEntityStatusCategory=None
            ),
            publicationDateBag=[google_data.publication_date] if google_data.publication_date else [],
            publicationSequenceNumberBag=[],
            publicationCategoryBag=[],
            docketNumber=None,
            firstInventorToFileIndicator=None,
            firstApplicantName=None,
            firstInventorName=google_data.inventors[0] if google_data.inventors else None,
            applicationConfirmationNumber=None,
            applicationStatusDate=None,
            applicationStatusDescriptionText=None,
            filingDate=google_data.filing_date,
            effectiveFilingDate=google_data.filing_date,
            grantDate=google_data.grant_date,
            groupArtUnitNumber=None,
            applicationTypeCode=None,
            applicationTypeLabelName=None,
            applicationTypeCategory=None,
            inventionTitle=google_data.title,
            patentNumber=google_data.patent_number,
            applicationStatusCode=None,
            earliestPublicationNumber=google_data.publication_number,
            earliestPublicationDate=google_data.publication_date,
            pctPublicationNumber=None,
            pctPublicationDate=None,
            internationalRegistrationPublicationDate=None,
            internationalRegistrationNumber=None,
            examinerNameText=None,
            class_=None,
            subclass=None,
            class_subclass=None,
            customerNumber=None,
            cpcClassificationBag=GooglePatentsAdapter._extract_cpc_codes(google_data),
            applicantBag=[],
            inventorBag=GooglePatentsAdapter._create_inventor_bag(google_data)
        )

    @staticmethod
    def _extract_cpc_codes(google_data: GooglePatentData) -> list:
        """Extract CPC classification codes."""
        cpc_codes = []
        for classification in google_data.classifications:
            if classification.get('type') == 'CPC':
                cpc_codes.append(classification.get('code', ''))
        return cpc_codes

    @staticmethod
    def _create_inventor_bag(google_data: GooglePatentData) -> list:
        """Create list of InventorBag from inventor names."""
        inventor_bags = []

        for inventor_name in google_data.inventors:
            # Try to parse name into parts
            parts = inventor_name.split()
            first_name = parts[0] if len(parts) > 0 else None
            last_name = parts[-1] if len(parts) > 1 else None
            middle_name = ' '.join(parts[1:-1]) if len(parts) > 2 else None

            inventor_bag = InventorBag(
                correspondenceAddressBag=[],
                firstName=first_name,
                middleName=middle_name,
                lastName=last_name,
                namePrefix=None,
                nameSuffix=None,
                preferredName=inventor_name,
                countryCode=None,
                inventorNameText=inventor_name
            )
            inventor_bags.append(inventor_bag)

        return inventor_bags

    @staticmethod
    def _create_event_data_bag(google_data: GooglePatentData) -> list:
        """Create list of EventDataBag from legal events."""
        event_bags = []

        for event in google_data.legal_events:
            event_bag = EventDataBag(
                eventCode=event.get('code'),
                eventDescriptionText=event.get('description'),
                eventDate=event.get('date')
            )
            event_bags.append(event_bag)

        return event_bags

    @staticmethod
    def _create_pgpub_metadata(google_data: GooglePatentData) -> Optional[PgPubDocumentMetaData]:
        """Create PgPubDocumentMetaData if publication data exists."""
        if google_data.publication_number:
            return PgPubDocumentMetaData(
                productIdentifier="GOOGLE_PATENTS",
                zipFileName=None,
                fileCreateDateTime=None,
                xmlFileName=None,
                fileLocationURI=f"https://patents.google.com/patent/US{google_data.publication_number}"
            )
        return None

    @staticmethod
    def _create_grant_metadata(google_data: GooglePatentData) -> Optional[GrantDocumentMetaData]:
        """Create GrantDocumentMetaData if patent data exists."""
        if google_data.patent_number:
            return GrantDocumentMetaData(
                productIdentifier="GOOGLE_PATENTS",
                zipFileName=None,
                fileCreateDateTime=None,
                xmlFileName=None,
                fileLocationURI=f"https://patents.google.com/patent/US{google_data.patent_number}"
            )
        return None


# Helper class to mimic USPTO API response structure
@dataclass
class MockUSPTOResponse:
    """Mock USPTO API response for compatibility with existing code."""
    patentFileWrapperDataBag: list

    def __post_init__(self):
        """Ensure patentFileWrapperDataBag is a list."""
        if not isinstance(self.patentFileWrapperDataBag, list):
            self.patentFileWrapperDataBag = [self.patentFileWrapperDataBag]
