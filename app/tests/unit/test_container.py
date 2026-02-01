
import sys
import unittest
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.container import Container, get_container


class TestContainer(unittest.TestCase):
    def test_container_initialization(self):
        """Container should initialize all services with dependencies"""
        container = get_container()

        self.assertIsInstance(container, Container)

        # Check Repos
        self.assertIsNotNone(container.arac_repo)
        self.assertIsNotNone(container.sefer_repo)
        self.assertIsNotNone(container.sofor_repo)
        self.assertIsNotNone(container.yakit_repo)

        # Check Services
        self.assertIsNotNone(container.sefer_service)
        self.assertIsNotNone(container.yakit_service)
        self.assertIsNotNone(container.analiz_service)
        self.assertIsNotNone(container.import_service)
        self.assertIsNotNone(container.report_service)
        self.assertIsNotNone(container.arac_service)
        self.assertIsNotNone(container.sofor_service)

        # Check Injection (White-box testing)
        self.assertEqual(container.sefer_service.repo, container.sefer_repo)
        self.assertEqual(container.yakit_service.repo, container.yakit_repo)

        # Analiz Service Injection
        self.assertEqual(container.analiz_service.yakit_repo, container.yakit_repo)
        self.assertEqual(container.analiz_service.sefer_repo, container.sefer_repo)

        # Import Service Injection
        self.assertEqual(container.import_service.arac_repo, container.arac_repo)
        self.assertEqual(container.import_service.sefer_service, container.sefer_service)

if __name__ == '__main__':
    unittest.main()
