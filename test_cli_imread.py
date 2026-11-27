"""CLI 图像读取失败的回归测试。"""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(ROOT, "Cli_AutoVer.py")


class CliImreadFailureTest(unittest.TestCase):
    def test_missing_image_reports_friendly_error(self):
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        missing = os.path.join(ROOT, "test", "__no_such_image__.png")
        result = subprocess.run(
            [sys.executable, SCRIPT, missing],
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stderr = result.stderr.decode("utf-8", errors="replace")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("无法读取图像文件", stderr)
        self.assertNotIn("Traceback", stderr)
        self.assertNotIn("AttributeError", stderr)


if __name__ == "__main__":
    unittest.main()
