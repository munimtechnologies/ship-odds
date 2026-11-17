# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Munim, Inc. Written by AI agents working for MV2 of Munim, Inc.
"""Runs Ship Odds' JavaScript tests under Node and checks the Forge manifest and the agent skill.

The core (src/core/*.js) has no dependencies, so `node --test` needs no npm install.
"""
import json
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
        for k in keys:
            self.assertLessEqual(len(k), 23, k)  # Forge limit for function keys

    def test_agent_actions_declared(self):
        declared = set(re.findall(r"^    - key: (ship-odds-[\w-]+)\n      name: .*\n      function:", self.text, re.M))
        for ref in re.findall(r"^        - (ship-odds-[\w-]+)\s*$", self.text, re.M):
            self.assertIn(ref, declared)
        self.assertEqual(len(declared), 4)

    def test_agent_name_length_and_scopes(self):
        names = re.findall(r"rovo:agent:\n    - key: [\w-]+\n      name: (.+)", self.text)
        self.assertTrue(names and len(names[0].strip()) <= 30)
        mcp = re.findall(r"rovo:mcp:\n    - key: [\w-]+\n      name: (.+)", self.text)
        self.assertTrue(mcp and len(mcp[0].strip()) <= 30)
        self.assertIn("read:jira-work", self.text)
        self.assertIn("storage:app", self.text)
        self.assertNotRegex(self.text, r"write:jira-work")

    def test_runtime_is_supported(self):
        # Forge accepts nodejs20.x, nodejs22.x and nodejs24.x (manifest reference, checked 2026-11-17).
        self.assertRegex(self.text, r"(?m)^    name: nodejs(20|22|24)\.x$")
        mem = re.search(r"(?m)^    memoryMB: (\d+)$", self.text)
        if mem:
            self.assertTrue(128 <= int(mem.group(1)) <= 1024)

    def test_timeout_only_on_trigger(self):
        # timeoutSeconds only affects scheduled triggers and async consumers.
        self.assertEqual(len(re.findall(r"timeoutSeconds:", self.text)), 1)
        self.assertRegex(self.text, r"handler: index\.gradeDaily\n\s+timeoutSeconds: \d+")

    def test_prompt_resource_exists(self):
        self.assertTrue(os.path.exists(os.path.join(HERE, "prompts", "agent.md")))
        self.assertTrue(os.path.exists(os.path.join(HERE, "src", "frontend", "index.jsx")))

    def test_license_metadata(self):
        with open(os.path.join(HERE, "package.json"), encoding="utf-8") as f:
            self.assertIn('"license": "Apache-2.0"', f.read())
        with open(os.path.join(HERE, "LICENSE"), encoding="utf-8") as f:
            self.assertIn("Apache License", f.read())


class PackageTests(unittest.TestCase):
    def test_dependencies_are_pinned(self):
        # A Marketplace / Codegeist build must be reproducible: exact versions, no "latest" or ranges.
        with open(os.path.join(HERE, "package.json"), encoding="utf-8") as f:
            pkg = json.load(f)
        deps = pkg.get("dependencies", {})
        self.assertIn("@forge/react", deps)
        for name, ver in deps.items():
            self.assertRegex(ver, r"^\d+\.\d+\.\d+$", "%s is not pinned: %s" % (name, ver))
        self.assertRegex(pkg["version"], r"^\d+\.\d+\.\d+$")


class SkillTests(unittest.TestCase):
    def test_skill_frontmatter_and_tools(self):
        path = os.path.join(HERE, "skills", "ship-odds", "SKILL.md")
        with open(path, encoding="utf-8") as f:
            text = f.read().replace("\r\n", "\n")
        m = re.match(r"---\n(.*?)\n---\n", text, re.S)
        self.assertTrue(m, "SKILL.md needs YAML frontmatter")
        self.assertRegex(m.group(1), r"(?m)^name: ship-odds$")
        self.assertRegex(m.group(1), r"(?m)^description: .{40,1024}$")
        with open(os.path.join(HERE, "manifest.yml"), encoding="utf-8") as f:
            manifest = f.read().replace("\r\n", "\n")
        tools = re.search(r"rovo:mcp:\n(?:.*\n)*?      tools:\n((?:        - .+\n)+)", manifest).group(1)
        for tool in re.findall(r"- ([\w-]+)", tools):
            self.assertIn("`%s`" % tool, text, tool)


if __name__ == "__main__":
    unittest.main()
