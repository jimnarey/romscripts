#!/usr/bin/env python3
"""
FBNeo DAT Format Converter

Converts FBNeo DAT files from various formats to the MAME XML format:
- v1: Non-XML parenthetical format → MAME XML
- v2: Partial XML without datafile wrapper → MAME XML
- v3: Already complete MAME XML (copy as-is)

Usage:
    python fba_format_converter.py <input_dir> <output_dir>
    python fba_format_converter.py <input_file> <output_file>
"""

import os
import re
import sys
import argparse
from pathlib import Path


class FBAFormatConverter:
    """Converts FBNeo DAT files between different formats."""

    def __init__(self):
        self.xml_header = """<?xml version="1.0"?>
<!DOCTYPE datafile PUBLIC "-//FB Alpha//DTD ROM Management Datafile//EN" "http://www.logiqx.com/Dats/datafile.dtd">

<datafile>"""
        self.xml_footer = "</datafile>"

    def detect_format(self, content: str) -> str:
        """Detect the format of the input file."""
        content = content.strip()

        if content.startswith("<?xml") and "<datafile>" in content:
            return "v3"  # Complete MAME XML
        elif content.startswith("<game") or content.startswith("\t<game"):
            return "v2"  # Partial XML without wrapper
        elif content.startswith("game ("):
            return "v1"  # Non-XML parenthetical format
        else:
            raise ValueError("Unknown format detected")

    def convert_v1_to_xml(self, content: str) -> str:
        """Convert v1 parenthetical format to MAME XML."""
        lines = content.strip().split("\n")
        xml_lines = [self.xml_header]

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if line.startswith("game (") or line.startswith("resource ("):
                element_type = "game" if line.startswith("game (") else "resource"
                i, xml_block = self._parse_v1_block(lines, i, element_type)
                xml_lines.extend(xml_block)
            else:
                i += 1

        xml_lines.append(self.xml_footer)
        return "\n".join(xml_lines)

    def _parse_v1_block(self, lines: list[str], start_idx: int, element_type: str) -> tuple:
        """Parse a v1 game or resource block into XML."""
        xml_block = []
        attributes = {}
        child_elements = []

        i = start_idx + 1

        while i < len(lines):
            line = lines[i].strip()

            if line == ")":
                break
            elif line.startswith("rom ("):
                rom_xml = self._parse_v1_rom(line)
                child_elements.append(f"\t\t{rom_xml}")
            elif line.startswith("biosset ("):
                biosset_xml = self._parse_v1_biosset(line)
                child_elements.append(f"\t\t{biosset_xml}")
            else:
                attr_name, attr_value = self._parse_v1_attribute(line)
                if attr_name:
                    attributes[attr_name] = attr_value

            i += 1

        attrs_str = " ".join(
            f'{k}="{self._escape_xml(v)}"' for k, v in attributes.items() if k in ["name", "cloneof", "romof"]
        )
        xml_block.append(f"\t<{element_type} {attrs_str}>")

        for attr_name, attr_value in attributes.items():
            if attr_name not in ["name", "cloneof", "romof"]:
                xml_block.append(f"\t\t<{attr_name}>{self._escape_xml(attr_value)}</{attr_name}>")

        xml_block.extend(child_elements)

        xml_block.append(f"\t</{element_type}>")

        return i + 1, xml_block

    def _parse_v1_attribute(self, line: str) -> tuple:
        """Parse a v1 attribute line."""
        # Handle quoted values
        if '"' in line:
            match = re.match(r'\s*(\w+)\s+"([^"]*)"', line)
            if match:
                return match.group(1), match.group(2)

        # Handle unquoted values
        parts = line.split(None, 1)
        if len(parts) == 2:
            return parts[0], parts[1]

        return None, None

    def _parse_v1_rom(self, line: str) -> str:
        """Parse a v1 ROM line into XML."""
        attributes = {}

        content = re.sub(r"^rom\s*\(\s*|\s*\)$", "", line)

        tokens = content.split()
        i = 0
        while i < len(tokens):
            key = tokens[i]
            if i + 1 < len(tokens):
                value = tokens[i + 1]
                attributes[key] = value
                i += 2
            else:
                i += 1

        xml_attrs = []
        for attr in ["name", "size", "crc", "merge", "bios", "status"]:
            if attr in attributes:
                xml_attrs.append(f'{attr}="{self._escape_xml(attributes[attr])}"')

        return f'<rom {" ".join(xml_attrs)}/>'

    def _parse_v1_biosset(self, line: str) -> str:
        """Parse a v1 BIOS set line into XML."""
        attributes = {}

        content = re.sub(r"^biosset\s*\(\s*|\s*\)$", "", line)

        tokens = content.split()
        i = 0
        while i < len(tokens):
            key = tokens[i]
            if key == "default" and i + 1 < len(tokens):
                value = tokens[i + 1]
                attributes[key] = value
                i += 2
            elif i + 1 < len(tokens):
                value = tokens[i + 1]
                attributes[key] = value
                i += 2
            else:
                i += 1

        xml_attrs = []
        for attr in ["name", "description", "default"]:
            if attr in attributes:
                value = attributes[attr].strip('"')
                xml_attrs.append(f'{attr}="{self._escape_xml(value)}"')

        return f'<biosset {" ".join(xml_attrs)}/>'

    def convert_v2_to_xml(self, content: str) -> str:
        """Convert v2 partial XML to complete MAME XML."""
        content = content.strip()
        if not content.startswith("<?xml"):
            return f"{self.xml_header}\n{content}\n{self.xml_footer}"
        else:
            if "<datafile>" not in content:
                content = re.sub(r"<\?xml[^>]*\?>\s*", "", content)
                content = re.sub(r"<!DOCTYPE[^>]*>\s*", "", content)
                return f"{self.xml_header}\n{content}\n{self.xml_footer}"

        return content

    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters."""
        if not isinstance(text, str):
            text = str(text)

        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    def convert_file(self, input_path: str, output_path: str) -> None:
        """Convert a single file."""
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            format_type = self.detect_format(content)
            print(f"Converting {input_path} (format: {format_type}) -> {output_path}")
            if format_type == "v1":
                converted = self.convert_v1_to_xml(content)
            elif format_type == "v2":
                converted = self.convert_v2_to_xml(content)
            elif format_type == "v3":
                converted = content
                print("Already in MAME format, copying as-is")
            else:
                raise ValueError(f"Unsupported format: {format_type}")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(converted)
            print(f"  Successfully converted to {output_path}")
        except Exception as e:
            print(f"Error converting {input_path}: {e}")
            raise

    def convert_directory(self, input_dir: str, output_dir: str) -> None:
        """Convert all XML files in a directory."""
        input_path = Path(input_dir)
        output_path = Path(output_dir)

        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")

        output_path.mkdir(parents=True, exist_ok=True)

        xml_files = list(input_path.glob("*.xml"))
        if not xml_files:
            print(f"No XML files found in {input_dir}")
            return

        print(f"Found {len(xml_files)} XML files to convert")

        for xml_file in xml_files:
            output_file = output_path / xml_file.name
            self.convert_file(str(xml_file), str(output_file))


def main():
    parser = argparse.ArgumentParser(description="Convert FBNeo DAT files to MAME XML format")
    parser.add_argument("input", help="Input file or directory")
    parser.add_argument("output", help="Output file or directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    converter = FBAFormatConverter()

    try:
        if os.path.isfile(args.input):
            # Convert single file
            converter.convert_file(args.input, args.output)
        elif os.path.isdir(args.input):
            # Convert directory
            converter.convert_directory(args.input, args.output)
        else:
            print(f"Error: Input path '{args.input}' is neither a file nor a directory")
            return 1

    except Exception as e:
        print(f"Conversion failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
