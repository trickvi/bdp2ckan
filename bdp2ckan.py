# -*- coding: utf-8 -*-
# bdp2ckan.py - Send a budget data package to a CKAN instance
# Copyright (C) 2013 Tryggvi Björgvinsson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import click
import json
import jsonschema
import requests
import urlparse


def create_ckan_package_dict(descriptor):
    """
    Convert metadata from a data package to CKAN metadata
    """
    
    # Mapping between metadata keys of CKAN and Data package
    # This does not handle licenses (multiple licenses in the data package)
    # because CKAN does not support it
    ckan_mapping = [('name', 'name'), ('title', 'title'), ('url', 'homepage'),
                    ('version', 'version'), ('license_id', 'license'),
                    ('notes', 'description')]

    # Extract available CKAN metadata from the data package
    data_dict = {}
    for (ckan, dpkg) in ckan_mapping:
        if dpkg in descriptor:
            data_dict[ckan] = descriptor[dpkg]

    return data_dict


def create_ckan_resource_array(descriptor):
    """
    Create a CKAN resource array from data package resources
    """
    # Mapping between resource metadata keys of CKAN and Data package
    # name and path can be overwritten by title and url respectively
    resource_mapping = [('name', 'name'), ('name', 'title'),
                        ('description', 'description'), ('format', 'format'),
                        ('mimetype', 'mediatype'), ('size', 'bytes'),
                        ('hash', 'hash'), ('url', 'path'), ('url', 'url')]

    # Extract CKAN resources and associated metadata from data package
    resource_array = {'resources': []}
    for resource in descriptor['resources']:
        data_dict = {}
            
        for (ckan, dpkg) in resource_mapping:
            if dpkg in resource:
                data_dict[ckan] = resource[dpkg]
        resource_array['resources'].append(data_dict)

    return resource_array


def create_budget_data_package_extras(descriptor):
    """
    Create a CKAN extras array from budget data package specific metadata
    """
    # Mapping between metadata keys of CKAN extras and Budget data package
    # This requires these particular keys to be set on the CKAN instance
    # Mapping is excluded because that's just going to look really bad in CKAN
    bdp_mapping = [('granularity', 'granularity'), ('direction', 'direction'),
                   ('status', 'status'), ('country', 'countryCode')]

    # Extract budget data package metadata as CKAN extras metadata
    data_dict = {'extras':[]}
    for (ckan, dpkg) in bdp_mapping:
        if dpkg in descriptor:
            data_dict['extras'].append({'key': dpkg, 'value': descriptor[dpkg]})

    return data_dict


def submit_to_ckan(host, apikey, data):
    """
    Submit a CKAN data dictionary to a given host with a given api key
    """

    # Put together the api url and authorization headers and send the data
    package_create_url = urlparse.urljoin(host, '/api/action/package_create')
    headers = {'Authorization': apikey}
    response = requests.post(package_create_url, headers=headers, json=data)

    return (response.status_code, response.text)


@click.command()
@click.option('--schema', default=None, nargs=1, type=click.File('r'),
              help='Schema to validate against')
@click.option('--host', default='localhost', nargs=1,
              help='CKAN instance to upload to')
@click.option('--apikey', default=None, nargs=1,
              help='CKAN user API key of uploader')
@click.option('--organization', default=None, nargs=1,
              help='CKAN organisation the dataset should belong to')
@click.argument('datapackage')
def bdp2ckan(schema, host, apikey, organization, datapackage):
    """
    Import a budget data package into CKAN
    """

    # Get the datapackage descriptor file
    response = requests.get(datapackage)
    descriptor = response.json()

    # If a schema was provided, we validate the datapackage based on the schema
    if schema is not None:
        schema_obj = json.load(schema)
        jsonschema.validate(descriptor, schema_obj)

    # Extract CKAN metadata from the data package
    data_dict = create_ckan_package_dict(descriptor)
    if organization is not None:
        data_dict['owner_org'] = organization

    # Fix urls in resources because paths must be turned into urls
    # because we don't support file uploads.
    resources = create_ckan_resource_array(descriptor)
    for resource in resources['resources']:
        if 'url' in resource and not (
                resource['url'].startswith('http://') or
                resource['url'].startswith('https://')):
            resource['url'] = urlparse.urljoin(datapackage, resource['url'])

    # Add the data package descriptor file as a resource
    resources['resources'].append({
        'name': 'Data package',
        'description': 'The descriptor file for the data package',
        'url': datapackage})

    # Append the resources to the package. This allows us to create resources
    # at the same time as we create the package, but this limits us to linking
    # to resources (hence the fix above) instead of uploading. If we want to
    # upload, we need to create each resource on its own.
    data_dict.update(resources)

    # Add budget data package metadata as extras, this requires that the
    # CKAN instance will have a schema that accepts these extras
    data_dict.update(create_budget_data_package_extras(descriptor))

    (status, message) = submit_to_ckan(host, apikey, data_dict)
    if status != 200:
        raise IOError(
            'Unable to submit budget data package to CKAN: {0}'.format(
                message)
        )

if __name__ == '__main__':
    bdp2ckan()
