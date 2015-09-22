# BDP2CKAN

A proof of concept command line script capable of submitting a Budget Data Package to a CKAN instance. The CKAN instance must be able to store metadata extras. This should use the python [datapackage](https://pypi.python.org/pypi/datapackage/) library but doesn't because currently that library doesn't support budget data packages (but the work done for this could be used to improve the datapackage library). Anyways, onwards to the important stuff.

## Installation

As this is a proof of concept, this does not provide a nice python setup. You have to do manual stuff to get it working but it's not the end of the world; it's still kind of standard. Create a virtualenv (recommended) and pip install the requirements.

    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt

## Usage

To see how it works type:

    python bdp2ckan.py --help

But it's very simple. You basically just provide a schema file (we provide it for you because we're super nice), the CKAN host, your API key for that CKAN host and a link to the datapackage.json descriptor file.

    python bdp2ckan.py --schema schemas/0.3.0.json --host 'http://localhost:5000' --apikey <my-awesome-api-key> --organization <organization-id-or-name> https://raw.githubusercontent.com/os-data/boost-armenia/master/datapackage.json

## License

bdp2ckan is available under the GNU General Public License, version 3. See LICENCE for more details.