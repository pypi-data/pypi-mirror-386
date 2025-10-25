# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mn_translit import (
    latin_to_cyrillic, 
    cyrillic_to_latin, 
    number_to_words, 
    words_to_number,
    transliterate
)


def test_latin_to_cyrillic():
    assert latin_to_cyrillic("Mongolia") == "Монголиа"
    assert latin_to_cyrillic("Sain baina uu?") == "Сайн байна уу?"
    assert latin_to_cyrillic("Sainai") == "Сайнай"
    assert latin_to_cyrillic("oilgokh") == "ойлгох"
    assert latin_to_cyrillic("nom") == "ном"
    assert latin_to_cyrillic("ger") == "гэр"
    assert latin_to_cyrillic("khün") == "хүн"
    assert latin_to_cyrillic("tsagaan") == "цагаан"
    print("✓ Latin to Cyrillic tests passed")


def test_cyrillic_to_latin():
    assert cyrillic_to_latin("Монгол") == "Mongol"
    assert cyrillic_to_latin("Улаанбаатар") == "Ulaanbaatar"
    assert cyrillic_to_latin("сайн") == "sayn"
    assert cyrillic_to_latin("ном") == "nom"
    assert cyrillic_to_latin("гэр") == "ger"
    assert cyrillic_to_latin("хүн") == "khün"
    assert cyrillic_to_latin("цагаан") == "tsagaan"
    print("✓ Cyrillic to Latin tests passed")


def test_diphthongs():
    assert latin_to_cyrillic("ai") == "ай"
    assert latin_to_cyrillic("ei") == "эй"
    assert latin_to_cyrillic("ii") == "ий"
    assert latin_to_cyrillic("oi") == "ой"
    assert latin_to_cyrillic("Sainai") == "Сайнай"
    assert latin_to_cyrillic("oilgokh") == "ойлгох"
    print("✓ Diphthong tests passed")


def test_number_to_words():
    assert number_to_words(0) == "тэг"
    assert number_to_words(1) == "нэг"
    assert number_to_words(21) == "хорин нэг"
    assert number_to_words(31) == "гучин нэг"
    assert number_to_words(41) == "дөчин нэг"
    assert number_to_words(51) == "тавин нэг"
    assert number_to_words(61) == "жаран нэг"
    assert number_to_words(71) == "далан нэг"
    assert number_to_words(81) == "наян нэг"
    assert number_to_words(91) == "ерэн нэг"
    assert number_to_words(100) == "зуун"
    assert number_to_words(111) == "зуун арав нэг"
    assert number_to_words(230) == "хоёр зуун гучин"
    assert number_to_words(1000) == "мянга"
    assert number_to_words(2024) == "хоёр мянга хорин дөрөв"
    print("✓ Number to words tests passed")


def test_words_to_number():
    assert words_to_number("тэг") == 0
    assert words_to_number("нэг") == 1
    assert words_to_number("мянга") == 1000
    assert words_to_number("хорин нэг") == 21
    assert words_to_number("гучин нэг") == 31
    assert words_to_number("зуун арав нэг") == 111
    assert words_to_number("хоёр зуун гучин") == 230
    assert words_to_number("хоёр мянга хорин дөрөв") == 2024
    print("✓ Words to number tests passed")


def test_trans_num_latin_to_cyrillic():
    result = latin_to_cyrillic("Bi 21 nom baina", trans_num=True)
    assert "хорин нэг" in result
    assert "21" not in result
    
    result = latin_to_cyrillic("On 2024", trans_num=True)
    assert "хоёр мянга хорин дөрөв" in result
    
    result = latin_to_cyrillic("Une ni 100 tugrug", trans_num=True)
    assert "зуун" in result
    
    result = latin_to_cyrillic("Mongol khun")
    assert result == latin_to_cyrillic("Mongol khun", trans_num=True)
    
    print("✓ Latin to Cyrillic with trans_num tests passed")


def test_trans_num_false_by_default():
    result = latin_to_cyrillic("Bi 21 nom baina")
    assert "21" in result
    assert "хорин нэг" not in result
    print("✓ trans_num=False by default test passed")


def test_major_number_scales():
    assert number_to_words(100) == "зуун"
    assert number_to_words(1000) == "мянга"
    assert number_to_words(10000) == "түм"
    assert number_to_words(100000) == "бум"
    assert number_to_words(1000000) == "сая"
    print("✓ Major number scales tests passed")


def test_transliterate_function():
    assert transliterate("Mongolia", to_script='cyrillic') == "Монголиа"
    assert transliterate("Монгол", to_script='latin') == "Mongol"
    
    result = transliterate("On 2024", to_script='cyrillic', trans_num=True)
    assert "хоёр мянга хорин дөрөв" in result
    
    print("✓ Transliterate function tests passed")


def test_edge_cases():
    assert latin_to_cyrillic("") == ""
    assert cyrillic_to_latin("") == ""
    assert latin_to_cyrillic("123") == "123"
    assert latin_to_cyrillic("!@#$%") == "!@#$%"
    print("✓ Edge case tests passed")


def run_all_tests():
    print("=" * 60)
    print("Running mn-translit Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        test_latin_to_cyrillic,
        test_cyrillic_to_latin,
        test_diphthongs,
        test_number_to_words,
        test_words_to_number,
        test_trans_num_latin_to_cyrillic,
        test_trans_num_false_by_default,
        test_major_number_scales,
        test_transliterate_function,
        test_edge_cases,
    ]
    
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print("✗ {} failed: {}".format(test.__name__, str(e)))
            failed += 1
        except Exception as e:
            print("✗ {} error: {}".format(test.__name__, str(e)))
            failed += 1
    
    print()
    print("=" * 60)
    if failed == 0:
        print("All tests passed! ✓")
        print("=" * 60)
        return 0
    else:
        print("{} test(s) failed!".format(failed))
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
