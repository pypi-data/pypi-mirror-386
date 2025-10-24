from rdflib import Namespace
from urllib.parse import urljoin
from functools import cached_property
from typing import Literal

import rdflib
import requests
from rdflib.namespace import RDF

import logging


logger = logging.getLogger(__name__)


MADS_NS = Namespace('http://www.loc.gov/mads/rdf/v1#')


class LocAPI(object):
    """Wrapper for Library of Congress API.

    https://id.loc.gov/
    """

    # base url for URIs and API calls
    uri_base = 'http://id.loc.gov/authorities/'
    # Names Authorities base
    lcnaf_base = 'http://id.loc.gov/authorities/names/'
    # Subject Authorities base
    lcsh_base = 'http://id.loc.gov/authorities/subjects/'
    # Children's Subject Headings base
    lcsj_base = 'http://id.loc.gov/authorities/childrensSubjects/'
    # Medium of Performance Thesaurus for Music base
    lcmpt_base = 'http://id.loc.gov/authorities/performanceMediums/'
    # Demographic Group Terms base
    lcdgt_base = 'http://id.loc.gov/authorities/demographicTerms/'
    # Thesaurus for Graphic Materials base
    tgm_base = 'http://id.loc.gov/vocabulary/graphicMaterials/'
    # AFS Ethnographic Thesaurus base
    afset_base = 'http://id.loc.gov/vocabulary/ethnographicTerms/'
    # Genre/Form Terms base
    lcgft_base = 'http://id.loc.gov/authorities/genreForms/'
    # Real world entity base (used for queries)
    rwo_base = 'http://id.loc.gov/rwo/agents/'

    @classmethod
    def uri_from_id(cls, loc_id):
        """Generate a URL for performing initial queries"""
        return urljoin(cls.uri_base, loc_id)

    @classmethod
    def dataset_uri_from_id(cls, loc_id):
        """Generate a URI for RDF triples based on LoC dataset"""
        if loc_id.startswith('n'):
            return urljoin(cls.lcnaf_base, loc_id)
        elif loc_id.startswith('sh'):
            return urljoin(cls.lcsh_base, loc_id)
        elif loc_id.startswith('sj'):
            return urljoin(cls.lcsj_base, loc_id)
        elif loc_id.startswith('mp'):
            return urljoin(cls.lcmpt_base, loc_id)
        elif loc_id.startswith('dg'):
            return urljoin(cls.lcdgt_base, loc_id)
        elif loc_id.startswith('tgm'):
            return urljoin(cls.tgm_base, loc_id)
        elif loc_id.startswith('afset'):
            return urljoin(cls.afset_base, loc_id)
        elif loc_id.startswith('gf'):
            return urljoin(cls.lcgft_base, loc_id)
        else:
            # Throw error if URL malformed
            raise ValueError("""
            The ID does not conform to supported ID formats.
            Please verify the ID is correct.
            """)

    @classmethod
    def rwo_uri_from_id(cls, loc_id):
        """Generate RWO URI for linked data queries"""
        return urljoin(cls.rwo_base, loc_id)

    def suggest(self, query, authority: Literal[None, 'names', 'subjects'] = None):
        """Query LoC's suggest service API using left-anchored search. Returns
        a list of results, or an empty list for no results or an error.

        Querying the older Suggest 1.0 is not implemented.

        :param query: Search query (string)
        :param authority: LoC authority to search. Supports names or subjects
        """

        # Note dropdown search language from API docs. What do we need to do to implement this?
        if authority:
            base_url = urljoin(self.uri_base, f'{authority}/')
        else:
            # BUG: If no authority provided, can return results from authorities that are not
            # implemented (e.g. BIBFRAME)
            base_url = 'http://id.loc.gov/'

        suggest_param = 'suggest2'

        query_url = urljoin(base_url, suggest_param)
        # TODO: incorporate more parameters?
        params = {'q': query}
        response = requests.get(query_url, params=params)
        if response.status_code == requests.codes.ok:
            data = SRUResult(response.json())
            if data.total_results > 0:
                return data.records

        response.raise_for_status()

        return []

    # not very DRY since this largely repeats logic of suggest method
    # could these two be combined and search param for search type be provided?
    def search(self, query, authority: Literal[None, 'names', 'subjects']):
        """Query LoC's suggest service API using keyword search. Returns a
        list of search results, or an empty list for an error.

        :param query: Search query (string)
        :param authority: Authority to search ('names' or 'subjects')
        """
        # keyword search needs to require an authority, because otherwise
        # it returns many results from the resources authority
        query_url = f'{self.uri_base}{authority}/suggest2'

        params = {'q': query, 'searchtype': 'keyword'}
        response = requests.get(query_url, params=params)
        if response.status_code == requests.codes.ok:
            data = SRUResult(response.json())
            if data.total_results > 0:
                return data.records

        response.raise_for_status()

        return []

    def retrieve_label(self, label):
        """Query LoC's label retrieval API to return a URI from
        a known label"""

        # TODO: Allow authorities to be passed in query
        base_url = 'https://id.loc.gov/authorities/label/'
        query_url = urljoin(base_url, label)
        response = requests.get(query_url, allow_redirects=False)
        # successful query should return a redirect
        if response.status_code == 302:
            uri = response.headers['x-uri']
            identifier = uri.split('/')[-1]
            return identifier

        else:
            # TODO: Not covered by test suite. Implement test
            response.raise_for_status()


# Question: Does each dataset need its own representation?
class LocEntity(object):
    """Object to represent single LoC entity

    :param loc_id: LoC identifier (string)
    """

    def __init__(self, loc_id):
        # probably need to identify canonical ID from LoC dataset
        self.loc_id = loc_id
        self.uri = LocAPI.uri_from_id(loc_id)
        self.dataset_uri = LocAPI.dataset_uri_from_id(loc_id)

    @property
    def uriref(self):
        """LoC URI reference as instance of :class:`rdflib.URIRef`"""
        # Consider deprecating this - unless the instance can't be matched to a LoC
        # dataset, this is generally only used in HTTP requests, which should also
        # resolve with the dataset URI
        return rdflib.URIRef(self.uri)

    @property
    def dataset_uriref(self):
        """LoC URI reference that includes LCNAF dataset
        marker as instance of :class:`rdflib.URIRef`"""
        return rdflib.URIRef(self.dataset_uri)

    @cached_property
    def rdf(self):
        """LoC data for this entity as :class:`rdflib.Graph`"""
        graph = rdflib.Graph()
        # try to query dataset URI first if it exists - sometimes plain URI throws an error
        if self.dataset_uri:
            response = requests.get(self.dataset_uri, headers={'Accept': 'application/rdf+xml'})
        else:
            response = requests.get(self.uri, headers={'Accept': 'application/rdf+xml'})
        response.raise_for_status()  # raise HTTPError on bad requests
        graph.parse(data=response.text, format='xml')

        return graph

    @property
    def authoritative_label(self):
        """Authoritative entity label in English"""
        labels = self.rdf.objects(self.dataset_uriref, MADS_NS.authoritativeLabel)
        # Sometimes label is marked "en", sometimes no label
        for label in labels:
            if label.language == 'en' or label.language is None:
                return label

    @property
    def scheme_membership(self):
        """LoC scheme that represents this entity as instance of
        :class:`rdflib.URIRef`"""
        # TODO: In theory, this can value can be multiple. Find example
        return self.rdf.value(self.dataset_uriref, MADS_NS.isMemberOfMADSScheme)

    @property
    def instance_of(self):
        """Linked Data authorities that describe this entity as
        list of instances of :class:`rdflib.URIRef`"""
        instances = self.rdf.objects(self.dataset_uriref, RDF.type)
        return [i for i in instances]


class NameEntity(LocEntity):
    """Object to represent single entity from the
    LoC Name Authority File. Inherits :class:`LocEntity`.

    :param loc_id: LoC identifier (string)
    """

    @property
    def rwo_uri(self):
        return LocAPI.rwo_uri_from_id(self.loc_id)

    @property
    def rwo_uriref(self):
        """LoC RWO URI reference as instance of
        :class:`rdflib.URIRef`"""
        return rdflib.URIRef(self.rwo_uri)

    # chronological data
    # some ancient authors use "active" or "fl." instead of life dates
    # should be implemented in future work package
    @property
    def birthdate(self):
        """MADS birthday as :class:`rdflib.term.Literal`"""
        return self.rdf.value(self.rwo_uriref, MADS_NS.birthDate)

    @property
    def deathdate(self):
        """MADS deathdate as :class:`rdflib.term.Literal`"""
        return self.rdf.value(self.rwo_uriref, MADS_NS.deathDate)

    @property
    def birthyear(self):
        """birth year as `int`"""
        if self.birthdate:
            return self.year_from_edtf(str(self.birthdate))

    @property
    def deathyear(self):
        """death year as `int`"""
        if self.deathdate:
            return self.year_from_edtf(str(self.deathdate))

    @classmethod
    def year_from_edtf(cls, date):
        """Return just the year from EDTF date. Expects a string,
        returns an integer. Normalizes uncertain years. Supports
        negative dates. No support for partially unknown years."""
        negative = False
        # if the date starts with a dash, flag negative and delete
        if date.startswith('-'):
            date = date[1:]
            negative = True
        # need more robust parsing here for approximate dates
        edtf_year = date.split('-')[0]
        edtf_chars = ['~', '?', '%']
        for c in edtf_chars:
            edtf_year = edtf_year.replace(c, '')
        edtf_year = int(edtf_year)
        if negative:
            return -edtf_year
        return edtf_year


class SubjectEntity(LocEntity):
    """Object to represent single entity from the LoC
    Subject Headings authority. Inherits :class:`LocEntity`.

    :param loc_id: LoC identifier (string)
    """

    @property
    def components(self):
        """Components for LoC Complex subjects. If subject is
        complex, returns a list of :class:`SubjectEntity`
        and :class:`NameEntity` objects. If subject is simple,
        returns `None`.

        Currently does not support temporal elements.
        """
        # container list for results
        components = []
        # get blank node that identifies collectionList
        c_bnode = self.rdf.value(self.dataset_uriref, MADS_NS.componentList)
        # get rdflib.collection.Collection representing components
        components_rdf = rdflib.collection.Collection(self.rdf, c_bnode)
        for c in components_rdf:
            if isinstance(c, rdflib.URIRef):
                uri = c.split('/')[-1]
                if uri.startswith('n'):
                    entity = NameEntity(uri)
                    components.append(entity)
                elif uri.startswith('sh'):
                    entity = SubjectEntity(uri)
                    components.append(entity)
                else:
                    # Not covered by test suite
                    logger.warning(f'Unrecognized schema for URI: {c}')
            else:
                # Not covered by test suite
                temp_label = self.rdf.value(c, MADS_NS.authoritativeLabel)
                components.append(temp_label)

        if len(components) > 0:
            return components
        else:
            return None


class SRUResult(object):
    """SRU search result object, for use with :meth:`LocAPI.search`."""

    def __init__(self, data):
        self._results = data.get('hits', [])
        # LoC API is buggy and does not have
        # a reliable way to count results
        self.total_results = len(self._results)

    @cached_property
    def records(self):
        """List of results as :class:`SRUItem`."""
        return [SRUItem(r) for r in self._results]


class SRUItem(object):
    """Single item returned by a SRU search, for use with
    :meth:`LocAPI.search` and :class:`SRUResult`.
    """

    def __init__(self, data):
        self._data = data

    @property
    def uri(self):
        """LoC URI for this result"""
        return self._data['uri']

    @property
    def loc_id(self):
        """LoC ID string for this result"""
        return self._data['token']

    @property
    def label(self):
        """Authoritative label for this result"""
        return self._data['aLabel']
