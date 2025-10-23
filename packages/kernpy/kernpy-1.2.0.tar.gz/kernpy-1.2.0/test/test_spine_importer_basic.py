import unittest
import logging
import sys

import kernpy as kp


class BasicSpineImporterTest(unittest.TestCase):
    """Used to test individual tokens"""

    def do_test_token_exported(self, input_encoding, expected):
        importer = kp.BasicSpineImporter()
        token = importer.import_token(input_encoding)
        self.assertIsNotNone(token)
        self.assertEqual(expected, token.export())

        return token

    def do_test_token_category(self, input_encoding, expected_category):
        importer = kp.BasicSpineImporter()
        token = importer.import_token(input_encoding)
        self.assertIsNotNone(token)
        self.assertEqual(expected_category, token.category)

        return token

    def test_time_signature(self):
        self.do_test_token_exported("*M4/4", "*M4/4")
        self.do_test_token_category("*M4/4", kp.TokenCategory.TIME_SIGNATURE)

    def test_empty(self):
        self.do_test_token_exported("*", "*")
        self.do_test_token_category("*", kp.TokenCategory.EMPTY)

    def test_measure_0(self):
        encoding_input = "="
        self.do_test_token_exported(encoding_input, "=")
        self.do_test_token_category(encoding_input, kp.TokenCategory.BARLINES)

    def test_measure_1(self):
        encoding_input = "=:|!-"
        self.do_test_token_exported(encoding_input, "=:|!")
        self.do_test_token_category(encoding_input, kp.TokenCategory.BARLINES)

    def test_measure_2(self):
        encoding_input = "=="
        self.do_test_token_exported(encoding_input, "==")
        self.do_test_token_category(encoding_input, kp.TokenCategory.BARLINES)

    def test_measure_3(self):
        encoding_input = "=10"
        self.do_test_token_exported(encoding_input, "=")
        self.do_test_token_category(encoding_input, kp.TokenCategory.BARLINES)


    def test_note_rest_should_be_lyrics(self):
        encoding_input = "4e"
        self.do_test_token_exported(encoding_input, "4e")
        self.do_test_token_category(encoding_input, kp.TokenCategory.OTHER)


    def test_normal_lyrics(self):
        encoding_input = "Don't stop me now"
        self.do_test_token_exported(encoding_input, "Don't stop me now")
        self.do_test_token_category(encoding_input, kp.TokenCategory.OTHER)