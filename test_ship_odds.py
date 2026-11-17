# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. Written by AI agents working for MV2 of Munim, Inc.
"""Runs Ship Odds' JavaScript tests under Node and checks the Forge manifest.

The core (src/core/*.js) has no dependencies, so `node --test` needs no npm install.
"""
import os
import re
import shutil
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = ["test/forecast.test.js", "test/jql.test.js", "test/service.test.js"]


def node_cmd():
    node = shutil.which("node")
    if not node:
        raise unittest.SkipTest("node is not installed")
    # Older Node needs a flag to treat ESM-syntax .js files (no "type": "module") as modules.
    probe = subprocess.run([node, "--experimental-detect-module", "-e", "0"], capture_output=True)
    return [node, "--experimental-detect-module"] if probe.returncode == 0 else [node]


class NodeTests(unittest.TestCase):
    def test_node_suite(self):
        cmd = node_cmd() + ["--test"] + TESTS
        res = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True, timeout=300)
        out = res.stdout + "\n" + res.stderr
        self.assertEqual(res.returncode, 0, out[-6000:])
        self.assertRegex(out, r"fail 0")


class ManifestTests(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(HERE, "manifest.yml"), encoding="utf-8") as f:
            self.text = f.read().replace("\r\n", "\n")

    def test_handlers_exist(self):
        with open(os.path.join(HERE, "src", "index.js"), encoding="utf-8") as f:
            src = f.read()
        handlers = re.findall(r"handler:\s*index\.(\w+)", self.text)
        self.assertGreaterEqual(len(handlers), 6)
        for h in handlers:
            self.assertRegex(src, r"export (const|async function|function) %s\b" % h, h)

    def test_function_keys_resolve(self):
        keys = set(re.findall(r"^\s+- key: ([\w-]+)\n\s+handler:", self.text, re.M))
        used = set(re.findall(r"^\s+function: ([\w-]+)\s*$", self.text, re.M))
        self.assertTrue(used, "no function references found")
        self.assertTrue(used <= keys, used - keys)

    def test_agent_actions_declared(self):
        declared = set(re.findall(r"^    - key: (ship-odds-[\w-]+)\n      name: .*\n      function:", self.text, re.M))
        for ref in re.findall(r"^        - (ship-odds-[\w-]+)\s*$", self.text, re.M):
            self.assertIn(ref, declared)
        self.assertEqual(len(declared), 4)

    def test_agent_name_length_and_scopes(self):
        names = re.findall(r"rovo:agent:\n    - key: [\w-]+\n      name: (.+)", self.text)
        self.assertTrue(names and len(names[0].strip()) <= 30)
        self.assertIn("read:jira-work", self.text)
        self.assertIn("storage:app", self.text)
        self.assertNotRegex(self.text, r"write:jira-work")

    def test_prompt_resource_exists(self):
        self.assertTrue(os.path.exists(os.path.join(HERE, "prompts", "agent.md")))
        self.assertTrue(os.path.exists(os.path.join(HERE, "src", "frontend", "index.jsx")))

    def test_license_metadata(self):
        with open(os.path.join(HERE, "package.json"), encoding="utf-8") as f:
            self.assertIn('"license": "Apache-2.0"', f.read())
        with open(os.path.join(HERE, "LICENSE"), encoding="utf-8") as f:
            self.assertIn("Apache License", f.read())


if __name__ == "__main__":
    unittest.main()
