import sys
from pathlib import Path


def test_package_root_on_sys_path():
    package_root = Path(__file__).resolve().parents[2]
    assert str(package_root) in sys.path


def test_function_module_reexports_utilities():
    from leksara import function as fn
    from leksara.functions.patterns.pii import replace_phone as impl_phone
    from leksara.functions.cleaner.basic import remove_tags as impl_remove_tags

    assert fn.replace_phone is impl_phone
    assert fn.remove_tags is impl_remove_tags
