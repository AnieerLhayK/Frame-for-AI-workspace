"""Guard the storage/authority dependency direction and compatibility imports."""
import subprocess
import sys
import unittest

class TaskRecordStoreImports(unittest.TestCase):
    def test_storage_import_does_not_load_authority_or_lifecycle(self):
        subprocess.run([sys.executable, '-c', "import sys; import scripts.workspace.task_record_store; assert 'scripts.workspace.agent_governance' not in sys.modules; assert 'scripts.workspace.task_records' not in sys.modules"], check=True)

    def test_facade_and_authority_import_in_both_orders(self):
        for modules in [('task_records', 'agent_governance'), ('agent_governance', 'task_records')]:
            with self.subTest(modules=modules):
                code = '; '.join('import scripts.workspace.' + name for name in modules)
                code += '; from scripts.workspace import task_records, task_record_store; assert task_records.read_record is task_record_store.read_record'
                subprocess.run([sys.executable, '-c', code], check=True)
