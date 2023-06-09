from django.test import TestCase
from .serializers import (
    ClientsCardSerializer,
    ContactsCardSerializer,
    ConnectInfoCardSerializer,
    BMServersCardSerializer,
    IntegrationCardSerializer,
)


class ClientsCardSerializerTestCase(TestCase):
    def test_serialization(self):
        serializer = ClientsCardSerializer()
        self.assertIsNotNone(serializer)

class ContactsCardSerializerTestCase(TestCase):
    def test_serialization(self):
        serializer = ContactsCardSerializer()
        self.assertIsNotNone(serializer)

class ConnectInfoCardSerializerTestCase(TestCase):
    def test_serialization(self):
        serializer = ConnectInfoCardSerializer()
        self.assertIsNotNone(serializer)

class BMServersCardSerializerTestCase(TestCase):
    def test_serialization(self):
        serializer = BMServersCardSerializer()
        self.assertIsNotNone(serializer)

class IntegrationCardSerializerTestCase(TestCase):
    def test_serialization(self):
        serializer = IntegrationCardSerializer()
        self.assertIsNotNone(serializer)
