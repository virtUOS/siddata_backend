"""
Functions for collecting educational resources called by cronjob
"""
import hashlib
from backend.models import Origin, InheritingCourse, WebResource, EducationalResource
from sickle import Sickle
import xml.etree.ElementTree as ET
import vobject
from django.conf import settings
import requests
from django.core.exceptions import ImproperlyConfigured
from urllib.parse import urljoin
import re

FORMAT_CHOICES = []
for format_choice_index in EducationalResource.FORMAT_CHOICES:
    FORMAT_CHOICES += [format_choice_index[0].casefold()]

def get_corresponding_format_tag(tag):
    tags = FORMAT_CHOICES
    for index in tags:
        target = index[1].casefold()
        if ' ' in target:
            target = re.split(' ',target)[0]
        if tag == target:
            return index[0]
    return None

def process_format_tag(dc):
    format_split = re.split('/', dc['format'])
    if format_split[-1] == 'pdf':
        return format_split[-1].upper()
    else:
        tag = None
        for item in format_split:
            item = item.casefold()
            tag = get_corresponding_format_tag(item)
            if tag is not None:
                break
        return tag

def collect_educational_resources():
    collect_oers()
    collect_moocs()


def collect_oers():
    for key, repository in settings.OER_REPOS.items():
        collect_edu_sharing_resources(repository['BASE_URL'])


def collect_moocs():
    if not settings.MOOC_CLIENTS:
        raise ImproperlyConfigured("MOOC clients are not not set")
    if 'UDEMY' in settings.MOOC_CLIENTS.keys():
        collect_udemy_courses()


def collect_udemy_courses():
    client_dict = settings.MOOC_CLIENTS['UDEMY']

    if client_dict['USER'] is None or client_dict['PASSWORD'] is None:
        raise ImproperlyConfigured("MOOC source 'UDEMY' is not configured. "
                                   "Either configure it or remove it from the settings.")

    base_url = client_dict['BASE_URL']
    route = 'courses'
    url = urljoin(client_dict['API_URL'], route)

    fields = [
        'id',
        'title',
        'url',
        'headline',
        'visible_instructors',
        'image_240x135'
    ]
    params = {
        'price': 'price-free',
        'is_affiliate_agreed': False,
        'is_deals_agreed': False,
        'fields[course]': ','.join(fields)
    }

    origin, origin_created = Origin.objects.get_or_create(
        name='udemy.com',
        type='mooc_provider',
        api_endpoint=client_dict['API_URL']
    )

    while True:
        response = requests.get(
            url,
            auth=(client_dict['USER'], client_dict['PASSWORD']),
            params=params
        )

        if response.status_code == 403:
            raise ImproperlyConfigured("Authentication for udemy client failed. "
                                       "Please check the configuration in settings.py.")

        if response.status_code != 200:
            print(f"Could not access udemy API. Failed with status code {response.status_code}")
            return

        data = response.json()

        # break condition for simulated do-while loop
        if 'results' not in data.keys() or not data['results']:
            break

        for c in data['results']:
            InheritingCourse.objects.update_or_create(
                identifier=c['id'],
                origin=origin,
                course_origin_id=c['id'],
                defaults={
                    'contributor': [],
                    'coverage': "",
                    'creator': c['visible_instructors'],
                    'date': None,
                    'description': c['headline'],
                    'format': ['CRS'],
                    'language': None,  # TODO
                    'publisher': origin.name,
                    'source': urljoin(base_url, c['url']),
                    'subject': c['curriculum_items'] + c['curriculum_lectures'],
                    'title': c['title'],
                    'type': ['udemy', 'mooc']
                }
            )

        url = data['next']
        if not url:
            break

        # since the next url already holds the url parameters we can empty the respective variable
        params = {}


def collect_edu_sharing_resources(repository):
    # Get all resources by using oai service
    sickle = Sickle(repository + "/edu-sharing/eduservlet/oai/provider")
    records = sickle.ListRecords(metadataPrefix='lom')

    # xml namespaces
    ns = {"oai": "http://www.openarchives.org/OAI/2.0/",
          "lom": "http://ltsc.ieee.org/xsd/LOM"}

    origin, origin_created = Origin.objects.get_or_create(
        name=repository,
        type='edu-sharing_provider',
    )

    for record in records:
        # Parse LOM-XML
        root = ET.fromstring(record.raw)
        header = root.find("oai:header", ns)
        lom = root.find(".//lom:lom", ns)

        dc = map_lom_to_dc(lom, ns)
        dc['format'] = process_format_tag(dc)

        try:
            EducationalResource.objects.update_or_create(
                identifier=dc["identifier"],
                origin=origin,
                defaults={
                    "contributor": dc["contributor"],
                    "coverage": dc["coverage"],
                    "creator": dc["creator"],
                    "date": dc["date"],
                    "description": dc["description"],
                    "format": dc["format"],
                    "language": dc["language"],
                    "publisher": dc["publisher"],
                    "relation": dc["relation"],
                    "rights": dc["rights"],
                    "source": dc["source"],
                    "subject": dc["subject"],
                    "title": dc["title"],
                    "type": ['OER'],
                }
            )
        except WebResource.MultipleObjectsReturned:
            # Ensure database consistency
            wrs = WebResource.objects.filter(identifier=dc["identifier"], origin=origin)
            wr = wrs[0]

            for to_delete in wrs[1:]:
                to_delete.delete()

            wr.contributor = dc["contributor"]
            wr.coverage = dc["coverage"]
            wr.creator = dc["creator"]
            wr.date = dc["date"]
            wr.description = dc["description"]
            wr.format = dc["format"]
            wr.language = dc["language"]
            wr.publisher = dc["publisher"]
            wr.relation = dc["relation"]
            wr.rights = dc["rights"]
            wr.source = repository
            wr.subject = dc["subject"]
            wr.title = dc["title"]
            wr.type = ['OER']
            wr.save()


def map_lom_to_dc(lom, ns):
    """
    Maps lom to Dublin Core partially based on
    https://www.researchgate.net/figure/Mapping-between-Unqualified-Dublin-Core-and-IEEE-LOM_tbl1_221425064
    param: lom - parsed lom xml element
           ns - dictionary of xml namespaces (e.g. {"lom": "http://ltsc.ieee.org/xsd/LOM"})
    """

    # collect creator
    vcard_creator = lom.findtext(".//lom:metaMetadata/lom:contribute[lom:role='creator']/lom:entity", namespaces=ns)
    creator = extract_name_from_vcard(vcard_creator)

    # collect publisher
    vcard_publisher = lom.findtext(".//lom:lifeCycle/lom:contribute[lom:role='publisher']/lom:entity", namespaces=ns)
    publisher = extract_name_from_vcard(vcard_publisher)

    # collect contributors
    vcard_contributors = list(
        elem.text for elem in lom.findall(".//lom:lifeCycle/lom:contribute/lom:entity", namespaces=ns))
    contributors = []
    for vcard in vcard_contributors:
        name = extract_name_from_vcard(vcard)
        if name:
            contributors.append(name)
    # add creator to list of contributors if not present
    if creator and creator not in contributors:
        contributors.append(creator)

    # collect coverage
    coverage = lom.findtext(".//lom:general/lom:coverage/string", namespaces=ns)
    # collect taxon if coverage doesn't exist
    if not coverage:
        coverage = list(elem.text for elem in lom.findall(
            ".//lom:classification/lom:taxonPath/lom:taxon/lom:entry/string", namespaces=ns))

    source = lom.findtext(".//lom:technical/lom:location", namespaces=ns)
    title = lom.findtext(".//lom:general/lom:title/string", namespaces=ns)

    identifier = lom.findtext(".//lom:general/lom:identifier/lom:entry", namespaces=ns)
    if identifier is None:
        identifier = hashlib.sha256((source + title).encode('utf-8')).hexdigest()

    return {
        "identifier": identifier,
        "contributor": contributors,
        "coverage": coverage,
        "creator": creator,
        "date": lom.findtext(".//lom:lifeCycle/lom:contribute/lom:date", namespaces=ns),
        "description": lom.findtext(".//lom:general/lom:description/string", namespaces=ns),
        "format": lom.findtext(".//lom:technical/lom:format", namespaces=ns),
        "language": lom.findtext(".//lom:general/lom:language", namespaces=ns),
        "publisher": publisher,
        "relation": lom.findtext(".//lom:relation/lom:resource/lom:description/string", namespaces=ns),
        "rights": lom.findtext(".//lom:rights/lom:description/string", namespaces=ns),
        "source": source,
        "subject": list(lom.find(".//lom:general/lom:keyword", namespaces=ns).itertext()),
        "title": title,
        "type": list(lom.find(".//lom:educational/lom:learningResourceType", namespaces=ns).itertext()),
    }


def extract_name_from_vcard(vcard):
    if vcard:
        v = vobject.readOne(vcard)
        try:
            return v.fn.value
        except AttributeError:
            return ""
