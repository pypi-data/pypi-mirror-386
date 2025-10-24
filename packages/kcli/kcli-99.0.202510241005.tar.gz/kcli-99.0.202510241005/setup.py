# coding=utf-8
from setuptools import setup, find_packages

import os
INSTALL = ['argcomplete', 'PyYAML', 'prettytable', 'jinja2', 'libvirt-python>=2.0.0']
AWS = ['boto3']
AZURE = ['azure-mgmt-compute', 'azure-mgmt-network', 'azure-mgmt-core', 'azure-identity', 'azure-mgmt-resource',
         'azure-mgmt-marketplaceordering', 'azure-storage-blob', 'azure-mgmt-dns', 'azure-mgmt-containerservice',
         'azure-mgmt-storage', 'azure-mgmt-msi', 'azure-mgmt-authorization']
HCLOUD = ['hcloud']
GCP = ['google-api-python-client', 'google-auth-httplib2', 'google-cloud-dns', 'google-cloud-storage',
       'google-cloud-container', 'google-cloud-compute']
OPENSTACK = ['python-cinderclient', 'python-neutronclient', 'python-glanceclient', 'python-keystoneclient',
             'python-novaclient', 'python-swiftclient']
OVIRT = ['ovirt-engine-sdk-python']
PROXMOX = ['proxmoxer']
VSPHERE = ['pyvmomi', 'cryptography']
IBMCLOUD = ['google-crc32c==1.1.2', 'ibm_vpc', 'ibm-cos-sdk', 'ibm-platform-services', 'ibm-cloud-networking-services']
EXTRAS = ['pyghmi', 'podman', 'websockify']
ALL = EXTRAS + AWS + GCP + OPENSTACK + OVIRT + VSPHERE + IBMCLOUD + AZURE + HCLOUD + PROXMOX

description = 'Provisioner/Manager for Libvirt/Vsphere/Aws/Gcp/Hcloud/Kubevirt/Ovirt/Openstack/IBM Cloud and containers'
long_description = description
if os.path.exists('README.rst'):
    long_description = open('README.rst').read()

setup(
    name='kcli',
    version='99.0.202510241005',
    include_package_data=True,
    packages=find_packages(),
    zip_safe=False,
    description=description,
    long_description=long_description,
    url='http://github.com/karmab/kcli',
    author='Karim Boumedhel',
    author_email='karimboumedhel@gmail.com',
    license='ASL',
    install_requires=INSTALL,
    extras_require={
        'all': ALL,
        'libvirt': [],
        'aws': AWS,
        'azure': AZURE,
        'gcp': GCP,
        'hcloud': HCLOUD,
        'ibm': IBMCLOUD,
        'openstack': OPENSTACK,
        'ovirt': OVIRT,
        'proxmox': PROXMOX,
        'vsphere': VSPHERE
    },
    entry_points='''
        [console_scripts]
        kcli=kvirt.cli:cli
        kweb=kvirt.web.main:run
        klist.py=kvirt.klist:main
        kmcp=kvirt.kmcp:main
        ksushy=kvirt.ksushy.main:run
        ekstoken=kvirt.ekstoken:cli
        gketoken=kvirt.gketoken:cli
    ''',
)
