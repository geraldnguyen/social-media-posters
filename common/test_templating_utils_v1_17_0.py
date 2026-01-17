import os
import unittest
from unittest.mock import patch, Mock
from templating_utils import process_templated_contents


class TestTemplatingUtilsV1_17_0(unittest.TestCase):
    """Test cases for v1.17.0 features:
    1. Optional parentheses following function name
    2. json.expression as function parameters
    3. The 'or' operation
    """

    def setUp(self):
        os.environ.pop('CONTENT_JSON', None)
        self.json_url = 'https://example.com/data.json'
        os.environ['CONTENT_JSON'] = self.json_url

    def tearDown(self):
        os.environ.pop('CONTENT_JSON', None)

    # ===== Test optional parentheses =====
    
    @patch('templating_utils.requests.get')
    def test_optional_parens_prefix(self, mock_get):
        """Test each:prefix without parentheses"""
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "genres": ["Mythology", "Tragedy", "Supernatural"]
        }
        # With parentheses (existing syntax)
        content1 = "@{json.genres | each:prefix('#') | join(' ')}"
        result1, = process_templated_contents(content1)
        self.assertEqual(result1, "#Mythology #Tragedy #Supernatural")
        
        # Without parentheses (new v1.17.0 syntax)
        content2 = "@{json.genres | each:prefix '#' | join ' '}"
        result2, = process_templated_contents(content2)
        self.assertEqual(result2, "#Mythology #Tragedy #Supernatural")

    @patch('templating_utils.requests.get')
    def test_optional_parens_join(self, mock_get):
        """Test join without parentheses"""
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "tags": ["python", "automation", "testing"]
        }
        # With parentheses
        content1 = "@{json.tags | join(', ')}"
        result1, = process_templated_contents(content1)
        self.assertEqual(result1, "python, automation, testing")
        
        # Without parentheses
        content2 = "@{json.tags | join ', '}"
        result2, = process_templated_contents(content2)
        self.assertEqual(result2, "python, automation, testing")

    @patch('templating_utils.requests.get')
    def test_optional_parens_join_while(self, mock_get):
        """Test join_while without parentheses"""
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "items": ["one", "two", "three", "four"]
        }
        # With parentheses
        content1 = "@{json.items | join_while(' ', 10)}"
        result1, = process_templated_contents(content1)
        self.assertEqual(result1, "one two")
        
        # Without parentheses (comma optional)
        content2 = "@{json.items | join_while ' ' 10}"
        result2, = process_templated_contents(content2)
        self.assertEqual(result2, "one two")

    # ===== Test json.expression as parameters =====

    @patch('templating_utils.requests.get')
    def test_json_expression_as_prefix_parameter(self, mock_get):
        """Test using json.expression as prefix parameter"""
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "series": "Aesop",
            "fables": ["The Fox and the Grapes", "The Tortoise and the Hare"]
        }
        # Use json.series as the prefix value
        content = "@{json.fables | each:prefix json.series | join(', ')}"
        result, = process_templated_contents(content)
        self.assertEqual(result, "AesopThe Fox and the Grapes, AesopThe Tortoise and the Hare")

    @patch('templating_utils.requests.get')
    def test_json_expression_as_prefix_parameter_no_parens(self, mock_get):
        """Test using json.expression as prefix parameter without parentheses"""
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "prefix": "Item-",
            "items": ["A", "B", "C"]
        }
        # Use json.prefix as the prefix value, no parentheses
        content = "@{json.items | each:prefix json.prefix | join ', '}"
        result, = process_templated_contents(content)
        self.assertEqual(result, "Item-A, Item-B, Item-C")

    @patch('templating_utils.requests.get')
    def test_json_expression_as_join_parameter(self, mock_get):
        """Test using json.expression as join separator"""
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "separator": " | ",
            "words": ["alpha", "beta", "gamma"]
        }
        # Use json.separator as the join separator
        content = "@{json.words | join(json.separator)}"
        result, = process_templated_contents(content)
        self.assertEqual(result, "alpha | beta | gamma")

    @patch('templating_utils.requests.get')
    def test_json_expression_as_join_parameter_no_parens(self, mock_get):
        """Test using json.expression as join separator without parentheses"""
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "delimiter": " - ",
            "items": ["one", "two", "three"]
        }
        # Use json.delimiter as the join separator, no parentheses
        content = "@{json.items | join json.delimiter}"
        result, = process_templated_contents(content)
        self.assertEqual(result, "one - two - three")

    # ===== Test 'or' operation =====

    @patch('templating_utils.requests.get')
    def test_or_operation_truthy_left(self, mock_get):
        """Test 'or' operation when left-hand-side is truthy"""
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "youtube_link": "https://youtube.com/watch?v=123",
            "permalink": "https://example.com/article"
        }
        # youtube_link is truthy, should return it
        content = "@{json.youtube_link | or(json.permalink)}"
        result, = process_templated_contents(content)
        self.assertEqual(result, "https://youtube.com/watch?v=123")

    @patch('templating_utils.requests.get')
    def test_or_operation_falsy_left_use_right(self, mock_get):
        """Test 'or' operation when left-hand-side is falsy (empty string)"""
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "youtube_link": "",
            "permalink": "https://example.com/article"
        }
        # youtube_link is empty, should return permalink
        content = "@{json.youtube_link | or(json.permalink)}"
        result, = process_templated_contents(content)
        self.assertEqual(result, "https://example.com/article")

    @patch('templating_utils.requests.get')
    def test_or_operation_null_left_use_right(self, mock_get):
        """Test 'or' operation when left-hand-side is null"""
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "youtube_link": None,
            "permalink": "https://example.com/article"
        }
        # youtube_link is null, should return permalink
        content = "@{json.youtube_link | or(json.permalink)}"
        result, = process_templated_contents(content)
        self.assertEqual(result, "https://example.com/article")

    @patch('templating_utils.requests.get')
    def test_or_operation_blank_left_use_right(self, mock_get):
        """Test 'or' operation when left-hand-side is blank (whitespace)"""
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "youtube_link": "   ",
            "permalink": "https://example.com/article"
        }
        # youtube_link is blank, should return permalink
        content = "@{json.youtube_link | or(json.permalink)}"
        result, = process_templated_contents(content)
        self.assertEqual(result, "https://example.com/article")

    @patch('templating_utils.requests.get')
    def test_or_operation_chained(self, mock_get):
        """Test chained 'or' operations for coalesce behavior"""
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "primary": "",
            "secondary": "",
            "tertiary": "fallback-value"
        }
        # Chain multiple or operations
        content = "@{json.primary | or(json.secondary) | or(json.tertiary)}"
        result, = process_templated_contents(content)
        self.assertEqual(result, "fallback-value")

    @patch('templating_utils.requests.get')
    def test_or_operation_chained_first_truthy(self, mock_get):
        """Test chained 'or' stops at first truthy value"""
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "primary": "",
            "secondary": "second-value",
            "tertiary": "third-value"
        }
        # Should stop at secondary and not evaluate tertiary
        content = "@{json.primary | or(json.secondary) | or(json.tertiary)}"
        result, = process_templated_contents(content)
        self.assertEqual(result, "second-value")

    @patch('templating_utils.requests.get')
    def test_or_operation_with_literal_string(self, mock_get):
        """Test 'or' operation with literal string as fallback"""
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "optional_field": ""
        }
        # Use literal string as fallback
        content = "@{json.optional_field | or('default-value')}"
        result, = process_templated_contents(content)
        self.assertEqual(result, "default-value")

    @patch('templating_utils.requests.get')
    def test_or_operation_no_parens(self, mock_get):
        """Test 'or' operation without parentheses"""
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "youtube_link": "",
            "permalink": "https://example.com/article"
        }
        # Without parentheses
        content = "@{json.youtube_link | or json.permalink}"
        result, = process_templated_contents(content)
        self.assertEqual(result, "https://example.com/article")

    # ===== Combined tests =====

    @patch('templating_utils.requests.get')
    def test_combined_features(self, mock_get):
        """Test combining all v1.17.0 features"""
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = {
            "title": "The Myth of Tereus and Procne",
            "url": "/stories/mythology/the-myth-of-tereus-and-procne/",
            "permalink": "https://tellstory.net/stories/mythology/the-myth-of-tereus-and-procne/",
            "youtube_link": "",
            "date": "2025-08-05",
            "genres": ["Mythology", "Tragedy", "Supernatural"],
            "tag_prefix": "#",
            "separator": " ",
            "description": "a short description"
        }
        # Combine: json expressions as params, no parens, or operation
        content = "@{json.description}, @{json.youtube_link | or json.permalink} @{json.genres | each:prefix json.tag_prefix | join json.separator}"
        result, = process_templated_contents(content)
        self.assertEqual(
            result, 
            "a short description, https://tellstory.net/stories/mythology/the-myth-of-tereus-and-procne/ #Mythology #Tragedy #Supernatural"
        )


if __name__ == '__main__':
    unittest.main()
