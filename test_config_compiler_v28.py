import unittest
import sys
import io
from config_compiler_v28 import ConfigCompilerV28

class TestConfigCompilerV28(unittest.TestCase):
    
    def setUp(self):
        self.compiler = ConfigCompilerV28()
    
    def test_parse_octal(self):
        self.assertEqual(self.compiler.parse_octal("755"), 493)
        self.assertEqual(self.compiler.parse_octal("30"), 24)
        self.assertEqual(self.compiler.parse_octal("777"), 511)
        self.assertEqual(self.compiler.parse_octal("0"), 0)
    
    def test_parse_string(self):
        self.assertEqual(self.compiler.parse_value("[[Hello]]"), "Hello")
        self.assertEqual(self.compiler.parse_value("[[Test String]]"), "Test String")
    
    def test_parse_struct(self):
        struct_expr = "struct { key1 = [[value1]], key2 = @[oo]10 }"
        result = self.compiler.parse_struct_value(struct_expr)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("key1"), "value1")
    
    def test_constant_reference(self):
        self.compiler.constants = {"default_value": 100}
        self.compiler.current_line = 1
        result = self.compiler.parse_value("!(default_value)")
        self.assertEqual(result, 100)
    
    def test_name_validation(self):
        self.compiler.current_line = 1
        self.compiler.parse_constant("invalid-name is [[test]]")
        self.assertGreater(len(self.compiler.errors), 0)
        
        self.compiler.errors = []
        self.compiler.parse_constant("validname is [[test]]")
        self.assertEqual(len(self.compiler.errors), 0)
    
    def test_comment_removal(self):
        content = """- Однострочный комментарий
key is [[value]]
%{
Многострочный
комментарий
%}
another is @[oo]777"""
        cleaned = self.compiler.remove_comments(content)
        self.assertNotIn("- Однострочный комментарий", cleaned)
        self.assertNotIn("%{", cleaned)
        self.assertNotIn("%}", cleaned)
        self.assertIn("key is [[value]]", cleaned)
    
    def test_nested_struct(self):
        config = """config is struct {
    server = struct {
        port = @[oo]8080,
        host = [[localhost]]
    },
    database = struct {
        name = [[test_db]],
        pool_size = @[oo]10
    }
}"""
        self.compiler.current_line = 1
        result = self.compiler.parse_struct_value(config[6:])
        self.assertIsInstance(result, dict)
        self.assertIn("server", result)
        self.assertIsInstance(result["server"], dict)
    
    def test_toml_formatting(self):
        self.assertEqual(self.compiler.format_toml_value(123), "123")
        self.assertEqual(self.compiler.format_toml_value("test"), '"test"')
        
        test_dict = {"key": "value", "number": 456}
        toml_str = self.compiler.format_toml_value(test_dict)
        self.assertIn('key = "value"', toml_str)
        self.assertIn("number = 456", toml_str)
    
    def test_full_parse(self):
        input_text = """app_name is [[Test App]]
port is @[oo]777
config is struct {
    debug = true,
    timeout = @[oo]30
}"""
        
        old_stdin = sys.stdin
        sys.stdin = io.StringIO(input_text)
        
        try:
            compiler = ConfigCompilerV28()
            success = compiler.compile()
            self.assertTrue(success)
            self.assertEqual(len(compiler.errors), 0)
        finally:
            sys.stdin = old_stdin

if __name__ == "__main__":
    unittest.main()