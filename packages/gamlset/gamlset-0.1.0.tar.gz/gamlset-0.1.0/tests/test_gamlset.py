import unittest
from dataclasses import dataclass
from gamlset import GamlObj, GamlSet


class GamlSet_TestCase(unittest.TestCase):
    """GamlSet 핵심 기능 테스트"""

    def test_gamlset_creates_new_type(self):
        """GamlSet에 GamlObj를 할당하면 새로운 타입이 생성되는지 확인"""
        class TestObj(GamlObj):
            pass

        class TestSet(GamlSet):
            TYPE_1 = TestObj

        # 새로운 타입이 생성되었는지 확인
        self.assertIsInstance(TestSet.TYPE_1, type)
        self.assertTrue(issubclass(TestSet.TYPE_1, GamlObj))
        self.assertTrue(issubclass(TestSet.TYPE_1, TestObj))

    def test_type_naming_convention(self):
        """생성된 타입 이름이 'OwnerName__FieldName' 형식인지 확인"""
        class SimpleObj(GamlObj):
            pass

        class MySet(GamlSet):
            FIELD_A = SimpleObj

        # 타입 이름 검증
        self.assertEqual(MySet.FIELD_A.__name__, "MySet__FIELD_A")

    def test_owner_and_name_attributes(self):
        """생성된 타입에 owner와 name 속성이 올바르게 설정되는지 확인"""
        class AttributeObj(GamlObj):
            pass

        class OwnerSet(GamlSet):
            ITEM = AttributeObj

        # owner 확인
        self.assertEqual(OwnerSet.ITEM.owner, OwnerSet)
        # name 확인
        self.assertEqual(OwnerSet.ITEM.name, "ITEM")

    def test_gamlobj_dict(self):
        """gamlobj_dict에 타입들이 올바르게 저장되는지 확인"""
        class DictObj(GamlObj):
            pass

        class DictSet(GamlSet):
            TYPE_1 = DictObj
            TYPE_2 = DictObj

        # gamlobj_dict에 타입들이 저장되어 있는지 확인
        self.assertIn("TYPE_1", DictSet.gamlobj_dict)
        self.assertIn("TYPE_2", DictSet.gamlobj_dict)
        self.assertEqual(len(DictSet.gamlobj_dict), 2)

    def test_instance_creation(self):
        """GamlSet에서 생성된 타입으로 인스턴스를 만들 수 있는지 확인"""
        @dataclass
        class InstanceObj(GamlObj):
            value: int
            message: str

        class InstanceSet(GamlSet):
            TEST_TYPE = InstanceObj

        # 인스턴스 생성
        instance = InstanceSet.TEST_TYPE(value=42, message="hello")

        # 인스턴스 검증
        self.assertIsInstance(instance, InstanceSet.TEST_TYPE)
        self.assertEqual(instance.value, 42)
        self.assertEqual(instance.message, "hello")


if __name__ == "__main__":
    unittest.main()
