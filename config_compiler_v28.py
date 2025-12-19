import sys
import re

class ConfigCompilerV28:
    def __init__(self):
        self.constants = {}
        self.errors = []
        self.current_line = 0
        self.output_lines = []
    
    def parse_stdin(self):
        content = sys.stdin.read()
        content = self.remove_comments(content)
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            self.current_line = i + 1
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('struct'):
                self.parse_struct(line, lines, i)
            elif 'is' in line:
                self.parse_constant(line)
    
    def remove_comments(self, content):
        while '%{' in content and '%}' in content:
            start = content.find('%{')
            end = content.find('%}', start) + 2
            content = content[:start] + content[end:]
        
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.strip().startswith('-'):
                line = ''
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def parse_struct(self, line, all_lines, start_idx):
        if not line.endswith('}'):
            self.errors.append(f"Строка {self.current_line}: Не завершен struct")
            return
        
        struct_content = line[6:-1].strip()
        if struct_content:
            self.parse_struct_content(struct_content)
        else:
            brace_count = 1
            struct_lines = []
            
            for j in range(start_idx + 1, len(all_lines)):
                current_line = all_lines[j].strip()
                self.current_line = j + 1
                
                brace_count += current_line.count('{')
                brace_count -= current_line.count('}')
                
                if brace_count == 0:
                    break
                
                struct_lines.append(current_line)
            
            if struct_lines:
                struct_content = '\n'.join(struct_lines)
                self.parse_struct_content(struct_content)
    
    def parse_struct_content(self, content):
        lines = [l.strip() for l in content.split('\n') if l.strip()]
        
        for line in lines:
            if line.endswith(','):
                line = line[:-1]
            
            if '=' in line:
                parts = line.split('=', 1)
                key = parts[0].strip()
                value_expr = parts[1].strip()
                
                if not re.match(r'^[a-z]+$', key):
                    self.errors.append(f"Строка {self.current_line}: Неверное имя ключа '{key}'")
                    continue
                
                value = self.parse_value(value_expr)
                if value is not None:
                    self.output_lines.append(f"{key} = {self.format_toml_value(value)}")
    
    def parse_constant(self, line):
        if 'is' not in line:
            self.errors.append(f"Строка {self.current_line}: Ожидалось 'is'")
            return
        
        parts = line.split('is', 1)
        name = parts[0].strip()
        value_expr = parts[1].strip()
        
        if not re.match(r'^[a-z]+$', name):
            self.errors.append(f"Строка {self.current_line}: Неверное имя '{name}'")
            return
        
        if value_expr.startswith('!'):
            const_name = value_expr[1:].strip().strip('()')
            if const_name in self.constants:
                value = self.constants[const_name]
                self.constants[name] = value
                self.output_lines.append(f"{name} = {self.format_toml_value(value)}")
            else:
                self.errors.append(f"Строка {self.current_line}: Константа '{const_name}' не найдена")
        else:
            value = self.parse_value(value_expr)
            if value is not None:
                self.constants[name] = value
                self.output_lines.append(f"{name} = {self.format_toml_value(value)}")
    
    def parse_value(self, expr):
        expr = expr.strip()
        
        if not expr:
            return None
        
        if expr.startswith('@['):
            if ']' in expr:
                end_bracket = expr.find(']')
                number_part = expr[end_bracket + 1:]
                return self.parse_octal(number_part)
        
        if expr.startswith('[[') and expr.endswith(']]'):
            return expr[2:-2]
        
        if expr.startswith('struct'):
            return self.parse_struct_value(expr)
        
        if expr in self.constants:
            return self.constants[expr]
        
        self.errors.append(f"Строка {self.current_line}: Неизвестное выражение '{expr}'")
        return None
    
    def parse_octal(self, number_str):
        try:
            return int(number_str.strip(), 8)
        except ValueError:
            self.errors.append(f"Строка {self.current_line}: Неверное восьмеричное число '{number_str}'")
            return None
    
    def parse_struct_value(self, expr):
        if not expr.endswith('}'):
            self.errors.append(f"Строка {self.current_line}: Не завершен struct")
            return {}
        
        struct_content = expr[6:-1].strip()
        if not struct_content:
            return {}
        
        result = {}
        lines = [l.strip() for l in struct_content.split(',') if l.strip()]
        
        for line in lines:
            if '=' in line:
                parts = line.split('=', 1)
                key = parts[0].strip()
                value_expr = parts[1].strip()
                
                if not re.match(r'^[a-z]+$', key):
                    self.errors.append(f"Строка {self.current_line}: Неверное имя ключа '{key}'")
                    continue
                
                value = self.parse_value(value_expr)
                if value is not None:
                    result[key] = value
        
        return result
    
    def format_toml_value(self, value):
        if isinstance(value, int):
            return str(value)
        elif isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, dict):
            lines = ['{']
            for k, v in value.items():
                lines.append(f'  {k} = {self.format_toml_value(v)},')
            lines[-1] = lines[-1].rstrip(',')
            lines.append('}')
            return '\n'.join(lines)
        else:
            return str(value)
    
    def compile(self):
        self.parse_stdin()
        
        if self.errors:
            for error in self.errors:
                sys.stderr.write(f"Ошибка: {error}\n")
            return False
        
        for line in self.output_lines:
            sys.stdout.write(line + '\n')
        
        return True

def main():
    compiler = ConfigCompilerV28()
    success = compiler.compile()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()