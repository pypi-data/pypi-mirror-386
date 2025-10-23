# Transpiler Mate (c) 2025
# 
# Transpiler Mate is licensed under
# Creative Commons Attribution-ShareAlike 4.0 International.
# 
# You should have received a copy of the license along with this work.
# If not, see <https://creativecommons.org/licenses/by-sa/4.0/>.

from __future__ import annotations

from .. import TranspilerBaseModel
from datetime import date as date_aliased
from enum import Enum
from pydantic import (
    AnyUrl,
    Field,
    RootModel
)
from typing import (
    List,
    Literal,
    Optional,
    Union
)


class Identifier(TranspilerBaseModel):
    """
    The Identifier is a unique string that identifies a resource.
    """

    identifier_type: str = Field(..., alias="identifierType")
    identifier: str


class NameIdentifier(TranspilerBaseModel):
    """
    Uniquely identifies an individual or legal entity, according to various schemes.
    """

    name_identifier: Optional[str] = Field(
        None,
        alias="nameIdentifier",
        description="Uniquely identifies an individual or legal entity, according to various schemes.",
    )
    name_identifier_scheme: str = Field(
        ...,
        alias="nameIdentifierScheme",
        description="The name of the name identifier scheme.",
    )
    scheme_uri: Optional[AnyUrl] = Field(
        None, alias="schemeURI", description="The URI of the name identifier scheme."
    )


class Affiliation(TranspilerBaseModel):
    """
    The organizational or institutional affiliation of the creator.
    """

    affiliation_identifier: Optional[str] = Field(
        None,
        alias="affiliationIdentifier",
        description="Uniquely identifies the organizational affiliation of the creator.",
    )
    affiliation_identifier_scheme: Optional[str] = Field(
        None,
        alias="affiliationIdentifierScheme",
        description="The name of the affiliation identifier scheme",
    )
    scheme_uri: Optional[AnyUrl] = Field(
        None,
        alias="schemeURI",
        description="The URI of the affiliation identifier scheme.",
    )


class NameType(Enum):
    """
    The type of name.
    """

    ORGANIZATIONAL = "Organizational"
    PERSONAL = "Personal"


class Creator(TranspilerBaseModel):
    """
    The main researcher involved in producing the data, or the author of the publication.
    """

    name: str = Field(..., description="The full name of the creator.")
    name_type: Optional[NameType] = Field(None, alias="nameType")
    given_name: Optional[str] = Field(
        None,
        alias="givenName",
        description="The personal or first name of the creator.",
    )
    family_name: Optional[str] = Field(
        None, alias="familyName", description="The surname or last name of the creator."
    )
    name_identifiers: Optional[List[NameIdentifier]] = Field(
        None,
        alias="nameIdentifiers",
        description="Uniquely identifies an individual or legal entity, according to various schemes.",
    )
    affiliation: Optional[List[Affiliation]] = Field(
        None,
        description="The organizational or institutional affiliations of the creator.",
    )


class TitleType(Enum):
    """
    The type of Title (other than the Main Title).
    """

    ALTERNATIVE_TITLE = "AlternativeTitle"
    SUBTITLE = "Subtitle"
    TRANSLATED_TITLE = "TranslatedTitle"
    OTHER = "Other"


class Title(TranspilerBaseModel):
    """
    A name or title by which a resource is known. May be the title of a dataset or the name of a piece of software or an instrument.
    """

    title: str = Field(..., description="A name or title by which a resource is known")
    lang: Optional[str] = Field(None, description="The languages of the title.")
    title_type: Optional[TitleType] = Field(
        None,
        alias="titleType",
        description="The type of Title (other than the Main Title).",
    )


class Publisher(TranspilerBaseModel):
    """
    The name of the entity that holds, archives, publishes, prints, distributes, releases, issues, or produces the resource. This property will be used to formulate the citation, so consider the prominence of the role.
    """

    name: str = Field(
        ...,
        description="The name of the entity that holds, archives, publishes, prints, distributes, releases, issues, or produces the resource. This property will be used to formulate the citation, so consider the prominence of the role.",
    )
    publisher_identifier: Optional[str] = Field(
        None,
        alias="publisherIdentifier",
        description="Uniquely identifies the publisher, according to various schemes.",
    )
    publisher_identifier_scheme: Optional[str] = Field(
        None,
        alias="publisherIdentifierScheme",
        description="The name of the publisher identifier scheme.",
    )
    scheme_uri: Optional[AnyUrl] = Field(
        None,
        alias="schemeURI",
        description="The URI of the publisher identifier scheme.",
    )
    lang: Optional[str] = Field(None, description="The language used by the Publisher.")


class Subject(TranspilerBaseModel):
    """
    Subject, keyword, classification code, or key phrase describing the resource.
    """

    subject: str = Field(
        ...,
        description="Subject, keyword, classification code, or key phrase describing the resource.",
    )
    subject_scheme: Optional[str] = Field(
        None,
        alias="subjectScheme",
        description="The name of the subject scheme or classification code or authority if one is used.",
    )
    scheme_uri: Optional[AnyUrl] = Field(
        None, alias="schemeURI", description="The URI of the subject identifier scheme."
    )
    value_uri: Optional[AnyUrl] = Field(
        None, alias="valueURI", description="The URI of the subject term."
    )
    classification_code: Optional[str] = Field(
        None,
        alias="classificationCode",
        description="The classification code used for the subject term in the subject schemes.",
    )
    lang: Optional[str] = Field(None, description="The language used in the Subject.")


class ContributorType(Enum):
    """
    The type of contributor of the resource
    """

    CONTACT_PERSON = "ContactPerson"
    DATA_COLLECTOR = "DataCollector"
    DATA_CURATOR = "DataCurator"
    DATA_MANAGER = "DataManager"
    DISTRIBUTOR = "Distributor"
    EDITOR = "Editor"
    HOSTING_INSTITUTION = "HostingInstitution"
    PRODUCER = "Producer"
    PROJECT_LEADER = "ProjectLeader"
    PROJECT_MANAGER = "ProjectManager"
    PROJECT_MEMBER = "ProjectMember"
    REGISTRATION_AGENCY = "RegistrationAgency"
    REGISTRATION_AUTHORITY = "RegistrationAuthority"
    RELATED_PERSON = "RelatedPerson"
    RESEARCHER = "Researcher"
    RESEARCH_GROUP = "ResearchGroup"
    RIGHTS_HOLDER = "RightsHolder"
    SPONSOR = "Sponsor"
    SUPERVISOR = "Supervisor"
    TRANSLATOR = "Translator"
    WORK_PACKAGE_LEADER = "WorkPackageLeader"
    OTHER = "Other"


class Contributor(Creator):
    """
    The institution or person responsible for collecting, managing, distributing, or otherwise contributing to the development of the resource.
    """

    contributor_type: ContributorType = Field(..., alias="contributorType")


class DateType(Enum):
    """
    The type of date
    """

    ACCEPTED = "Accepted"
    AVAILABLE = "Available"
    COPYRIGHTED = "Copyrighted"
    COLLECTED = "Collected"
    COVERAGE = "Coverage"
    CREATED = "Created"
    ISSUED = "Issued"
    SUBMITTED = "Submitted"
    UPDATED = "Updated"
    VALID = "Valid"
    WITHDRAWN = "Withdrawn"
    OTHER = "Other"


class Date(TranspilerBaseModel):
    """
    Date relevant to the work.
    """

    date: date_aliased = Field(..., description="Date relevant to the work.")
    date_type: DateType = Field(..., alias="dateType", description="The type of date")
    date_information: Optional[str] = Field(
        None,
        alias="dateInformation",
        description="Specific information about the date, if appropriate.",
    )


class ResourceTypeGeneral(Enum):
    """
    The general type of a resource.
    """

    AUDIOVISUAL = "Audiovisual"
    AWARD = "Award"
    BOOK = "Book"
    BOOK_CHAPTER = "BookChapter"
    COLLECTION = "Collection"
    COMPUTATIONAL_NOTEBOOK = "ComputationalNotebook"
    CONFERENCE_PAPER = "ConferencePaper"
    CONFERENCE_PROCEEDING = "ConferenceProceeding"
    DATA_PAPER = "DataPaper"
    DATASET = "Dataset"
    DISSERTATION = "Dissertation"
    EVENT = "Event"
    IMAGE = "Image"
    INTERACTIVE_RESOURCE = "InteractiveResource"
    INSTRUMENT = "Instrument"
    JOURNAL = "Journal"
    JOURNAL_ARTICLE = "JournalArticle"
    MODEL = "Model"
    OUTPUT_MANAGEMENT_PLAN = "OutputManagementPlan"
    PEER_REVIEW = "PeerReview"
    PHYSICAL_OBJECT = "PhysicalObject"
    PREPRINT = "Preprint"
    PROJECT = "Project"
    REPORT = "Report"
    SERVICE = "Service"
    SOFTWARE = "Software"
    SOUND = "Sound"
    STANDARD = "Standard"
    STUDY_REGISTRATION = "StudyRegistration"
    TEXT = "Text"
    WORKFLOW = "Workflow"
    OTHER = "Other"


class ResourceType(TranspilerBaseModel):
    """
    A description of the resource.
    """

    resource_type: str = Field(
        ..., alias="resourceType", description="A description of the resource."
    )
    resource_type_general: ResourceTypeGeneral = Field(..., alias="resourceTypeGeneral")


class AlternateIdentifier(TranspilerBaseModel):
    """
    An identifier other than the primary Identifier applied to the resource being registered.
    """

    alternate_identifier: Optional[str] = Field(
        None,
        alias="alternateIdentifier",
        description="An identifier other than the primary Identifier applied to the resource being registered",
    )
    alternate_identifier_type: ResourceTypeGeneral = Field(
        ..., alias="alternateIdentifierType"
    )


class RelationType(Enum):
    """
    Description of the relationship of the resource being registered (A) and the related resource (B).
    """

    IS_CITED_BY = "IsCitedBy"
    CITES = "Cites"
    IS_SUPPLEMENT_TO = "IsSupplementTo"
    IS_SUPPLEMENTED_BY = "IsSupplementedBy"
    IS_CONTINUED_BY = "IsContinuedBy"
    CONTINUES = "Continues"
    IS_DESCRIBED_BY = "IsDescribedBy"
    DESCRIBES = "Describes"
    HAS_METADATA = "HasMetadata"
    IS_METADATA_FOR = "IsMetadataFor"
    HAS_VERSION = "HasVersion"
    IS_VERSION_OF = "IsVersionOf"
    IS_NEW_VERSION_OF = "IsNewVersionOf"
    IS_PREVIOUS_VERSION_OF = "IsPreviousVersionOf"
    IS_PART_OF = "IsPartOf"
    HAS_PART = "HasPart"
    IS_PUBLISHED_IN = "IsPublishedIn"
    IS_REFERENCED_BY = "IsReferencedBy"
    REFERENCES = "References"
    IS_DOCUMENTED_BY = "IsDocumentedBy"
    DOCUMENTS = "Documents"
    IS_COMPILED_BY = "IsCompiledBy"
    COMPILES = "Compiles"
    IS_VARIANT_FORM_OF = "IsVariantFormOf"
    IS_ORIGINAL_FORM_OF = "IsOriginalFormOf"
    IS_IDENTICAL_TO = "IsIdenticalTo"
    IS_REVIEWED_BY = "IsReviewedBy"
    REVIEWS = "Reviews"
    IS_DERIVED_FROM = "IsDerivedFrom"
    IS_SOURCE_OF = "IsSourceOf"
    IS_REQUIRED_BY = "IsRequiredBy"
    REQUIRES = "Requires"
    IS_OBSOLETED_BY = "IsObsoletedBy"
    OBSOLETES = "Obsoletes"
    IS_COLLECTED_BY = "IsCollectedBy"
    COLLECTS = "Collects"
    IS_TRANSLATION_OF = "IsTranslationOf"
    HAS_TRANSLATION = "HasTranslation"


class RelatedIdentifierType(Enum):
    """
    The type of the RelatedIdentifier.
    """

    ARK = "ARK"
    AR_XIV = "arXiv"
    BIBCODE = "bibcode"
    CSTR = "CSTR"
    DOI = "DOI"
    EAN13 = "EAN13"
    EISSN = "EISSN"
    HANDLE = "Handle"
    IGSN = "IGSN"
    ISBN = "ISBN"
    ISSN = "ISSN"
    ISTC = "ISTC"
    LISSN = "LISSN"
    LSID = "LSID"
    PMID = "PMID"
    PURL = "PURL"
    RRID = "RRID"
    UPC = "UPC"
    URL = "URL"
    URN = "URN"
    W3ID = "w3id"


class RelatedIdentifier(TranspilerBaseModel):
    """
    Identifier of related resources.
    """

    related_identifier: Optional[str] = Field(
        None, alias="relatedIdentifier", description="Identifier of related resources."
    )
    related_identifier_type: Optional[RelatedIdentifierType] = Field(
        None, alias="relatedIdentifierType"
    )
    relation_type: Optional[RelationType] = Field(None, alias="relationType")
    related_metadata_scheme: Optional[str] = Field(
        None, alias="relatedMetadataScheme", description="The name of the schemes."
    )
    scheme_uri: Optional[AnyUrl] = Field(
        None, alias="schemeURI", description="The URI of the name identifier scheme."
    )
    scheme_type: Optional[str] = Field(
        None,
        alias="schemeType",
        description="The type of the relatedMetadataScheme, linked with the schemeURI",
    )
    resource_type_general: Optional[ResourceTypeGeneral] = Field(
        None, alias="resourceTypeGeneral"
    )


class Right(TranspilerBaseModel):
    """
    Any right information for this resource.
    """

    rights: str = Field(..., description="Any right information for this resource.")
    rights_uri: Optional[AnyUrl] = Field(
        None, alias="rightsURI", description="The URI of the license."
    )
    rights_identifier: Optional[str] = Field(
        None,
        alias="rightsIdentifier",
        description="A short, standardized version of the license name.",
    )
    rights_identifier_scheme: Optional[str] = Field(
        None, alias="rightsIdentifierScheme", description="The name of the scheme."
    )
    scheme_uri: Optional[AnyUrl] = Field(
        None, alias="schemeURI", description="The URI of the rightsIdentifierScheme."
    )


class DescriptionType(Enum):
    """
    The type of the Description.
    """

    ABSTRACT = "Abstract"
    METHODS = "Methods"
    SERIES_INFORMATION = "SeriesInformation"
    TABLE_OF_CONTENTS = "TableOfContents"
    TECHNICAL_INFO = "TechnicalInfo"
    OTHER = "Other"


class Description(TranspilerBaseModel):
    """
    All additional information that does not fit in any of the other categories.
    """

    description: str = Field(
        ...,
        description="All additional information that does not fit in any of the other categories.",
    )
    description_type: DescriptionType = Field(
        ..., alias="descriptionType", description="The type of the Description."
    )


class GeoLocationPoint(TranspilerBaseModel):
    """
    A point location in space.
    """

    point_longitude: float = Field(
        ..., alias="pointLongitude", description="Longitudinal dimension of point."
    )
    point_latitude: float = Field(
        ..., alias="pointLatitude", description="Latitudinal dimension of point."
    )


class GeoLocationBox(TranspilerBaseModel):
    """
    The spatial limits of a box.
    """

    west_bound_longitude: float = Field(
        ...,
        alias="westBoundLongitude",
        description="Western longitudinal dimension of box.",
    )
    east_bound_longitude: float = Field(
        ...,
        alias="eastBoundLongitude",
        description="Eastern longitudinal dimension of box.",
    )
    south_bound_latitude: float = Field(
        ...,
        alias="southBoundLatitude",
        description="Southern latitudinal dimension of box.",
    )
    north_bound_latitude: float = Field(
        ...,
        alias="northBoundLatitude",
        description="Northern latitudinal dimension of box.",
    )


class GeoLocationPolygon(TranspilerBaseModel):
    """
    A drawn polygon area, defined by a set of points and lines connecting the points in a closed chain.
    """

    polygon_point: Optional[GeoLocationPoint] = Field(None, alias="polygonPoint")
    in_polygon_point: Optional[GeoLocationPoint] = Field(None, alias="inPolygonPoint")


class GeoLocation(TranspilerBaseModel):
    """
    Spatial region or named place where the data was gathered or about which the data is focused.
    """

    geo_location_point: Optional[GeoLocationPoint] = Field(
        None, alias="geoLocationPoint"
    )
    geo_location_box: Optional[GeoLocationBox] = Field(None, alias="geoLocationBox")
    geo_location_place: Optional[str] = Field(
        None,
        alias="geoLocationPlace",
        description="Description of a geographic location.",
    )
    geo_location_polygon: Optional[List[GeoLocationPolygon]] = Field(
        None, alias="geoLocationPolygon", min_length=4
    )


class FunderIdentifierType(Enum):
    """
    The type of the funderIdentifier.
    """

    CROSSREF_FUNDER_ID = "Crossref Funder ID"
    GRID = "GRID"
    ISNI = "ISNI"
    ROR = "ROR"
    OTHER = "Other"


class FundingReference(TranspilerBaseModel):
    """
    Information about financial support (funding) for the resource being registered.
    """

    funder_name: str = Field(
        ..., alias="funderName", description="Name of the funding provider."
    )
    funder_identifier: Optional[str] = Field(
        None,
        alias="funderIdentifier",
        description="Uniquely identifies a funding entity, according to various types",
    )
    funder_identifier_type: FunderIdentifierType = Field(
        ...,
        alias="funderIdentifierType",
        description="The type of the funderIdentifier.",
    )
    scheme_uri: Optional[AnyUrl] = Field(
        None, alias="schemeURI", description="The URI of the funder identifier scheme."
    )
    award_number: Optional[str] = Field(
        None,
        alias="awardNumber",
        description="The code assigned by the funder to a sponsored award (grant).",
    )
    award_uri: Optional[AnyUrl] = Field(
        None,
        alias="awardURI",
        description="The URI leading to a page provided by the funder for more information about the award (grant).",
    )
    award_title: Optional[str] = Field(
        None,
        alias="awardTitle",
        description="The human readable title or name of the award (grant).",
    )


class RelatedItemIdentifier(TranspilerBaseModel):
    """
    The identifier for the related item.
    """

    related_item_identifier_type: Optional[RelatedIdentifierType] = Field(
        None, alias="relatedItemIdentifierType"
    )
    related_metadata_scheme: Optional[str] = Field(
        None, alias="relatedMetadataScheme", description="The name of the schemes."
    )
    scheme_uri: Optional[AnyUrl] = Field(
        None, alias="schemeURI", description="The URI of the name identifier scheme."
    )
    scheme_type: Optional[str] = Field(
        None,
        alias="schemeType",
        description="The type of the relatedMetadataScheme, linked with the schemeURI",
    )


class RelatedItemCreator(TranspilerBaseModel):
    """
    The institution or person responsible for creating the related resource.
    """

    name: str = Field(..., description="The full name of the related item creator")
    name_type: Optional[NameType] = Field(None, alias="nameType")
    given_name: Optional[str] = Field(
        None,
        alias="givenName",
        description="The personal or first name of the creator.",
    )
    family_name: Optional[str] = Field(
        None, alias="familyName", description="The surname or last name of the creator."
    )


class RelatedItemTitle(TranspilerBaseModel):
    """
    Title of the related item.
    """

    title: str = Field(..., description="Title of the related item.")
    title_type: Optional[str] = Field(
        None, alias="titleType", description="Type of the related item title."
    )


class RelatedItemContributor(RelatedItemCreator):
    """
    An institution or person identified as contributing to the development of the resource.
    """

    contributor_type: ContributorType = Field(..., alias="contributorType")


class NumberType(Enum):
    """
    Type of the related item’s number, e.g., report number or article number.
    """

    ARTICLE = "Article"
    CHAPTER = "Chapter"
    REPORT = "Report"
    OTHER = "Other"


class PublicationYear1(RootModel[str]):
    root: str = Field(
        ...,
        description="The year when the data was or will be made publicly available.",
        pattern="^\\d{4}$",
    )


class Event(Enum):
    """
    Indicates a state-change action for the DOI
    """

    PUBLISH = "publish"
    REGISTER = "register"
    HIDE = "hide"


class RelatedItem(TranspilerBaseModel):
    """
    Information about a resource related to the one being registered.
    """

    related_item_type: ResourceTypeGeneral = Field(..., alias="relatedItemType")
    relation_type: ResourceTypeGeneral = Field(..., alias="relationType")
    related_item_identifier: Optional[RelatedItemIdentifier] = Field(
        None, alias="relatedItemIdentifier"
    )
    creators: Optional[List[RelatedItemCreator]] = Field(
        None,
        description="The institution or person responsible for creating the related resource.",
    )
    titles: List[RelatedItemTitle] = Field(
        ..., description="Title of the related item", min_length=1
    )
    publication_year: Optional[Union[int, PublicationYear1]] = Field(
        None,
        alias="publicationYear",
        description="The year when the data was or will be made publicly available.",
    )
    volume: Optional[str] = Field(None, description="Volume of the related item.")
    issue: Optional[str] = Field(
        None, description="Issue number or name of the related item."
    )
    number: Optional[str] = Field(
        None,
        description="Number of the resource within the related item, e.g., report number or article number.",
    )
    number_type: Optional[NumberType] = Field(
        None,
        alias="numberType",
        description="Type of the related item’s number, e.g., report number or article number.",
    )
    first_page: Optional[str] = Field(
        None,
        alias="firstPage",
        description="First page of the resource within the related item, e.g., of the chapter, article, or conference paper in proceedings.",
    )
    last_page: Optional[str] = Field(
        None,
        alias="lastPage",
        description="Last page of the resource within the related item, e.g., of the chapter, article, or conference paper in proceedings.",
    )
    publisher: Optional[str] = Field(
        None,
        description="The name of the entity that holds, archives, publishes prints, distributes, releases, issues, or produces the resource.",
    )
    edition: Optional[str] = Field(
        None, description="Edition or version of the related item."
    )
    contributors: Optional[List[RelatedItemContributor]] = Field(
        None,
        description="An institution or person identified as contributing to the development of the resource",
    )


class DataCiteAttributes(TranspilerBaseModel):
    """
    DataCite Metadata Schema
    """

    doi: Optional[str] = Field(None, description="The full DOI (prefix + suffix)")
    prefix: Optional[str] = Field(None, description="The namespace prefix")
    suffix: Optional[str] = Field(None, description="The suffix portion of the DOI")
    event: Optional[Event] = Field(
        None, description="Indicates a state-change action for the DOI"
    )
    identifiers: List[Identifier]
    creators: List[Creator] = Field(
        ...,
        description="The main researchers involved in producing the data, or the authors of the publication, in priority order.",
        min_length=1,
    )
    titles: List[Title] = Field(
        ...,
        description="Names or titles by which a resource is known. May be the title of a dataset or the name of a piece of software or an instrument.",
        min_length=1,
    )
    publisher: Publisher
    publication_year: Union[int, PublicationYear1] = Field(
        ...,
        alias="publicationYear",
        description="The year when the data was or will be made publicly available.",
    )
    subjects: Optional[List[Subject]] = Field(
        None,
        description="Subjects, keywords, classification codes, or key phrases describing the resource.",
    )
    contributors: Optional[List[Contributor]] = Field(
        None,
        description="The institution or person responsible for collecting, managing, distributing, or otherwise contributing to the development of the resource.",
    )
    dates: Optional[List[Date]] = Field(
        None, description="Different dates relevant to the work."
    )
    language: Optional[str] = Field(
        None, description="The primary language of the resource"
    )
    types: ResourceType
    alternate_identifiers: Optional[List[AlternateIdentifier]] = Field(
        None,
        alias="alternateIdentifiers",
        description="An identifier other than the primary Identifier applied to the resource being registered.",
    )
    related_identifiers: Optional[List[RelatedIdentifier]] = Field(
        None,
        alias="relatedIdentifiers",
        description="Identifiers of related resources.",
    )
    sizes: Optional[List[str]] = Field(
        None,
        description="Size (e.g., bytes, pages, inches, etc.) or duration (extent), e.g., hours, minutes, days, etc., of a resource.",
    )
    formats: Optional[List[str]] = Field(
        None, description="Technical format of the resources."
    )
    version: Optional[str] = Field(
        None, description="The version number of the resources."
    )
    rights_list: Optional[List[Right]] = Field(
        None, alias="rightsList", description="Any rights information for this resource"
    )
    descriptions: Optional[List[Description]]
    geo_locations: Optional[List[GeoLocation]] = Field(
        None,
        alias="geoLocations",
        description="Spatial regions or named places where the data was gathered or about which the data is focused.",
    )
    funding_references: Optional[List[FundingReference]] = Field(
        None,
        alias="fundingReferences",
        description="Information about financial support (funding) for the resource being registered.",
    )
    related_items: Optional[List[RelatedItem]] = Field(
        None,
        alias="relatedItems",
        description="Informations about a resource related to the one being registered.",
    )


class Data(TranspilerBaseModel):
    """
    TODO
    """

    id: str
    type: str
    attributes: Optional[DataCiteAttributes]


class DataCiteMetadata46(TranspilerBaseModel):
    """
    DataCite Metadata Schema
    """

    data: Data
