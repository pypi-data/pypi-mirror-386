#!/usr/bin/env python3
import os
import subprocess
import shutil
import sys
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class ProtobufGenerationHook(BuildHookInterface):
    """Generate protocol buffer Python files before building."""

    def initialize(self, version, build_data):
        """Run protobuf generation during the initialize phase."""
        self.generate_proto_files()
        return build_data

    def generate_proto_files(self):
        """Generate Python code from protobuf definitions."""
        # Get the project root directory
        project_dir = Path(self.root)

        # Define paths (hardcoded filepaths and packages. Ideally dynamically generated)
        proto_package_dir = project_dir / "proto" / "jitxcore" / "_proto"
        output_dir = project_dir / "src"

        # Ensure the output directory exists
        os.makedirs(str(output_dir), exist_ok=True)

        # Create __init__.py files to make the generated code importable
        os.makedirs(str(output_dir / "jitxcore" / "_proto"), exist_ok=True)
        with open(str(output_dir / "jitxcore" / "__init__.py"), "w") as f:
            f.write("# Generated package\n")
        with open(str(output_dir / "jitxcore" / "_proto" / "__init__.py"), "w") as f:
            f.write("# Generated package\n")

        # Copy version.py from src to jitxcore package
        version_source = output_dir / "version.py"
        version_dest = output_dir / "jitxcore" / "version.py"
        if version_source.exists():
            shutil.copy2(str(version_source), str(version_dest))
            print(f"Copied {version_source} to {version_dest}")
        else:
            print(f"Warning: version.py not found at {version_source}", file=sys.stderr)

        proto_files = list(proto_package_dir.glob("*.proto"))
        if not proto_files:
            print("No .proto files found in proto/jitxcore/_proto/", file=sys.stderr)
            sys.exit(1)

        print("Validating protoc version...")
        protoc = shutil.which("protoc")
        if protoc is None:
            print("Error: 'protoc' not found on PATH")
            sys.exit(1)

        PROTOC_MAJOR_VER_MINIMUM = 28  # protoc 28.0 and above

        try:
            result = subprocess.run(
                [protoc, "--version"], check=True, capture_output=True, text=True
            )
            # stdout should be like "libprotoc 30.0"
            ver = result.stdout.strip().removeprefix("libprotoc ").split(".")
            if (
                len(ver) > 0
                and ver[0].isdigit()
                and int(ver[0]) >= PROTOC_MAJOR_VER_MINIMUM
            ):
                print(
                    f"Protoc version {'.'.join(ver)} meets minimum version {PROTOC_MAJOR_VER_MINIMUM}.0.0"
                )
            else:
                print(
                    f"Error: Protoc version {'.'.join(ver)} is less than required version {PROTOC_MAJOR_VER_MINIMUM}.0.0"
                )
                sys.exit(1)
        except subprocess.CalledProcessError as e:
            print(f"Error validating protoc version: {e}", file=sys.stderr)
            sys.exit(1)

        # Run protoc command with directory pattern instead of explicit files
        cmd = [
            protoc,
            *[str(proto_file.relative_to(project_dir)) for proto_file in proto_files],
            "--python_out=src",
            "--pyi_out=src",
            "-Iproto",
        ]

        print(f"Running: {' '.join(cmd)}")

        try:
            subprocess.run(cmd, check=True)
            print("Protocol buffer code generation successful!")
        except subprocess.CalledProcessError as e:
            print(f"Error generating protocol buffer code: {e}", file=sys.stderr)
            sys.exit(1)
