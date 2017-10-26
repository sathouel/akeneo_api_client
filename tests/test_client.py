# -*- coding: utf-8 -*-

from akeneo_api_client.collection import *
from akeneo_api_client.resources import *
from akeneo_api_client.auth import Auth
from akeneo_api_client.utils import urljoin
from akeneo_api_client.client import *

import requests
from requests.auth import AuthBase
import unittest
import base64
import json
from time import time

import logging
import logzero
from logzero import logger

from vcr_unittest import VCRTestCase

import copy


class TestClient(VCRTestCase):
    client_id = '1_ovvscbaj0pwwg8sookkgkc8ck4kog8gscg8g44sc88c8w48ww'
    secret = 'rpi0wuiusa8okok4cw8kkkc4s488gc0sggkc0480wskkgkwo0'
    username = 'admin'
    password = 'admin'
    base_url = 'http://localhost:8080'

    def _get_vcr(self, **kwargs):
        logzero.loglevel(logging.INFO)
        myvcr = super(TestClient, self)._get_vcr(**kwargs)
        myvcr.match_on = ['method', 'path', 'query', 'body', 'headers']
        myvcr.record_mode='once'
        return myvcr

    def test_product_search(self):
        akeneo = Client(self.base_url,
            self.client_id, self.secret, self.username, self.password)
        pool = akeneo.products
        items = pool.fetch_list()
        self.assertEquals(len(items.get_list()), 10)

        items = pool.fetch_list(args={
            "search":{
                "short_description": [
                  {
                    "operator": "CONTAINS",
                    "value": "shoes",
                    "locale": "en_US",
                    "scope": "ecommerce"
                  }
                ]
            }
        })
        self.assertEquals(len(items.get_list()), 0)

        items = pool.fetch_list(args={
            "search":{
                "description": [
                  {
                    "operator": "CONTAINS",
                    "value": "print",
                    "locale": "en_US",
                    "scope": "ecommerce"
                  }
                ]
            }, "limit": 5
        })
        self.assertEquals(len(items.get_list()), 5)

        items = pool.fetch_list(args={
            "search":{
                "description": [
                  {
                    "operator": "CONTAINS",
                    "value": "print",
                    "locale": "en_US",
                    "scope": "ecommerce"
                  }
                ]
            }
        })
        self.assertEquals(len(items.get_list()), 10)
        listA = items.get_list()

        items = pool.fetch_list(args={
            "search":{
                "description": [
                  {
                    "operator": "CONTAINS",
                    "value": "print",
                    "locale": "en_US",
                    "scope": "ecommerce"
                  }
                ]
            },
            "search_scope": "ecommerce"
        })
        self.assertEquals(len(items.get_list()), 10)
        listB = items.get_list()
        self.assertTrue(listA == listB)

        items = pool.fetch_list(args={
            "pagination_type": "search_after",
            "limit": 15
        })
        self.assertEquals(len(items.get_list()), 15)
        iterator = iter(items)
        for i in range(25):
            item = next(iterator)
        self.assertEquals(len(items.get_list()), 30)


    def test_family_variants(self):
        akeneo = Client(self.base_url,
            self.client_id, self.secret, self.username, self.password)
        families = akeneo.families.fetch_list().get_list()
        for family in families:
            family_code = akeneo.families.get_code(family)
            variants_pool = akeneo.families.variants(family_code)
            variants = variants_pool.fetch_list().get_list()
            if family_code == 'clothing':
                self.assertEquals(len(variants), 5)
            if family_code == 'headphones':
                self.assertEquals(len(variants), 0)

    def test_attribute_options(self):
        akeneo = Client(self.base_url,
            self.client_id, self.secret, self.username, self.password)
        attributes = akeneo.attributes.fetch_list().get_list()
        for attribute in attributes:
            attribute_code = akeneo.attributes.get_code(attribute)
            options_pool = akeneo.attributes.options(attribute_code)
            logger.debug(options_pool._endpoint)
            if attribute_code in ['auto_exposure', 'auto_focus_assist_beam',
                'auto_focus_lock', 'auto_focus_modes', 'auto_focus_points',
                'camera_model_name', 'care_instructions']:
                # those don't have any option:
                # 404, "Attribute \"auto_exposure\" does not support options. Only attributes of type \"pim_catalog_simpleselect\", \"pim_catalog_multiselect\" support options."
                with self.assertRaises(requests.exceptions.HTTPError):
                    options = options_pool.fetch_list().get_list()
            else:
                options = options_pool.fetch_list().get_list()

    def test_association_types(self):
        akeneo = Client(self.base_url,
            self.client_id, self.secret, self.username, self.password)
        item = akeneo.association_types.fetch_item('PACK')
        self.assertIsNotNone(item)

    def test_products(self):
        akeneo = Client(self.base_url,
            self.client_id, self.secret, self.username, self.password)
        item = akeneo.products.fetch_item('1111111137')
        items = akeneo.products.fetch_list().get_list()
        self.assertIsNotNone(item)
        self.assertEquals(len(items), 10)

    def test_get_resources(self):
        akeneo = Client(self.base_url,
            self.client_id, self.secret, self.username, self.password)
        for name in akeneo.RESOURCE_NAMES:
            if name == 'published_products':
                # valid for EE only
                # TODO: implement tests against EE API
                pass
            else:
                pool = getattr(akeneo, name)
                items = pool.fetch_list().get_list()
                self.assertTrue(len(items) > 2)

    def test_client_auth_invalid(self):
        with self.assertRaises(ValueError):
            akeneo = Client(self.base_url, self.password)

    def test_client_auth_credential(self):
        akeneo = Client(self.base_url,
            self.client_id, self.secret, self.username, self.password)
        item = akeneo.products.fetch_item('1111111137')

    def test_client_auth_object(self):
        auth=Auth(self.base_url, self.client_id, self.secret,
            self.username, self.password)
        akeneo = Client(self.base_url, session=None,
            auth=auth)
        item = akeneo.products.fetch_item('1111111137')

    valid_product = """{"identifier":"myawesometshirt","enabled":true,"family":"clothing","categories":["master_men_blazers"],"groups":[],"parent":null,"values":{"collection":[{"data":["summer_2017"],"locale":null,"scope":null}],"color":[{"data":"white","locale":null,"scope":null}],"description":[{"data":"Biker jacket","locale":"en_US","scope":"ecommerce"}],"ean":[{"data":"1234567946367","locale":null,"scope":null}],"material":[{"data":"polyester","locale":null,"scope":null}],"name":[{"data":"Biker jacket","locale":null,"scope":null}],"price":[{"data":[{"amount":null,"currency":"EUR"},{"amount":null,"currency":"USD"}],"locale":null,"scope":null}],"size":[{"data":"xl","locale":null,"scope":null}],"variation_name":[{"data":"Biker jacket polyester","locale":"en_US","scope":null}]}}"""

    