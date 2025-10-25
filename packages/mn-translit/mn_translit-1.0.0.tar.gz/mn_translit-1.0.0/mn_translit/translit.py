# -*- coding: utf-8 -*-
from __future__ import unicode_literals


class MongolianTransliterator(object):
    
    LATIN_TO_CYRILLIC_MULTI = [
        ('kh', 'х'), ('ts', 'ц'), ('ch', 'ч'), ('sh', 'ш'),
        ('yo', 'ё'), ('yu', 'ю'), ('ya', 'я'), ('ye', 'е'), ('zh', 'ж'),
        ('ai', 'ай'), ('ei', 'эй'), ('ii', 'ий'), ('oi', 'ой'),
        ('Kh', 'Х'), ('KH', 'Х'), ('Ts', 'Ц'), ('TS', 'Ц'),
        ('Ch', 'Ч'), ('CH', 'Ч'), ('Sh', 'Ш'), ('SH', 'Ш'),
        ('Yo', 'Ё'), ('YO', 'Ё'), ('Yu', 'Ю'), ('YU', 'Ю'),
        ('Ya', 'Я'), ('YA', 'Я'), ('Ye', 'Е'), ('YE', 'Е'),
        ('Zh', 'Ж'), ('ZH', 'Ж'),
    ]
    
    LATIN_TO_CYRILLIC_SINGLE = {
        'a': 'а', 'b': 'б', 'v': 'в', 'g': 'г', 'd': 'д', 'e': 'э',
        'z': 'з', 'i': 'и', 'y': 'й', 'k': 'к', 'l': 'л', 'm': 'м',
        'n': 'н', 'o': 'о', 'p': 'п', 'r': 'р', 's': 'с', 't': 'т',
        'u': 'у', 'f': 'ф', 'h': 'х', 'c': 'ц', 'w': 'в',
        'A': 'А', 'B': 'Б', 'V': 'В', 'G': 'Г', 'D': 'Д', 'E': 'Э',
        'Z': 'З', 'I': 'И', 'Y': 'Й', 'K': 'К', 'L': 'Л', 'M': 'М',
        'N': 'Н', 'O': 'О', 'P': 'П', 'R': 'Р', 'S': 'С', 'T': 'Т',
        'U': 'У', 'F': 'Ф', 'H': 'Х', 'C': 'Ц', 'W': 'В',
        'ö': 'ө', 'ü': 'ү', 'Ö': 'Ө', 'Ü': 'Ү',
    }
    
    CYRILLIC_TO_LATIN = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'ye',
        'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k',
        'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'ө': 'ö', 'п': 'p',
        'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ү': 'ü', 'ф': 'f',
        'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'Ye',
        'Ё': 'Yo', 'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K',
        'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O', 'Ө': 'Ö', 'П': 'P',
        'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 'Ү': 'Ü', 'Ф': 'F',
        'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
    }
    
    NUMBERS = {
        0: 'тэг', 1: 'нэг', 2: 'хоёр', 3: 'гурав', 4: 'дөрөв', 5: 'тав',
        6: 'зургаа', 7: 'долоо', 8: 'найм', 9: 'ес', 10: 'арав',
        20: 'хорин', 30: 'гучин', 40: 'дөчин', 50: 'тавин', 60: 'жаран',
        70: 'далан', 80: 'наян', 90: 'ерэн', 100: 'зуун', 1000: 'мянга',
        10000: 'түм', 100000: 'бум', 1000000: 'сая', 1000000000: 'тэрбум',
        1000000000000: 'их наяд'
    }
    
    WORD_TO_NUMBER = {v: k for k, v in NUMBERS.items()}
    
    def _convert_numbers_in_text(self, text, to_words=True):
        import re
        if to_words:
            def replace_number(match):
                num = int(match.group())
                try:
                    return self.number_to_words(num)
                except:
                    return match.group()
            return re.sub(r'\d+', replace_number, text)
        else:
            words = text.split()
            result = []
            i = 0
            while i < len(words):
                word_lower = words[i].lower()
                if word_lower in self.WORD_TO_NUMBER or (i + 1 < len(words) and word_lower + ' ' + words[i + 1].lower() in ' '.join([w.lower() for w in words[i:i+3]])):
                    try:
                        num_words = []
                        j = i
                        while j < len(words) and words[j].lower() in self.WORD_TO_NUMBER:
                            num_words.append(words[j])
                            j += 1
                        if num_words:
                            num_text = ' '.join(num_words)
                            try:
                                num = self.words_to_number(num_text)
                                result.append(str(num))
                                i = j
                                continue
                            except:
                                pass
                    except:
                        pass
                result.append(words[i])
                i += 1
            return ' '.join(result)
    
    def latin_to_cyrillic(self, text, trans_num=False):
        if not text:
            return text
        
        if trans_num:
            text = self._convert_numbers_in_text(text, to_words=True)
        
        result, i = [], 0
        while i < len(text):
            matched = False
            if i + 2 <= len(text):
                substring = text[i:i+2]
                for latin, cyrillic in self.LATIN_TO_CYRILLIC_MULTI:
                    if substring == latin:
                        result.append(cyrillic)
                        i += 2
                        matched = True
                        break
            
            if not matched:
                char = text[i]
                result.append(self.LATIN_TO_CYRILLIC_SINGLE.get(char, char))
                i += 1
        
        return ''.join(result)
    
    def cyrillic_to_latin(self, text, trans_num=False):
        if not text:
            return text
        
        result = ''.join([self.CYRILLIC_TO_LATIN.get(char, char) for char in text])
        
        if trans_num:
            result = self._convert_numbers_in_text(result, to_words=False)
        
        return result
    
    def number_to_words(self, num):
        if not isinstance(num, int) or num < 0:
            raise ValueError("Number must be a positive integer")
        
        if num in self.NUMBERS:
            return self.NUMBERS[num]
        
        if num < 20:
            return self.NUMBERS[10] + ' ' + self.NUMBERS[num % 10]
        
        if num < 100:
            tens, ones = (num // 10) * 10, num % 10
            return self.NUMBERS[tens] if ones == 0 else self.NUMBERS[tens] + ' ' + self.NUMBERS[ones]
        
        if num < 1000:
            hundreds, remainder = num // 100, num % 100
            if hundreds == 1:
                result = self.NUMBERS[100]
            else:
                result = self.NUMBERS[hundreds] + ' ' + self.NUMBERS[100]
            if remainder >= 10:
                result += ' ' + self.number_to_words(remainder)
            elif remainder > 0:
                result += ' ' + self.NUMBERS[remainder]
            return result
        
        if num < 10000:
            thousands, remainder = num // 1000, num % 1000
            result = self.NUMBERS[thousands] + ' ' + self.NUMBERS[1000]
            return result if remainder == 0 else result + ' ' + self.number_to_words(remainder)
        
        if num < 100000:
            ten_thousands, remainder = num // 10000, num % 10000
            if ten_thousands == 1:
                result = self.NUMBERS[10000]
            else:
                result = self.number_to_words(ten_thousands) + ' ' + self.NUMBERS[10000]
            return result if remainder == 0 else result + ' ' + self.number_to_words(remainder)
        
        if num < 1000000:
            hundred_thousands, remainder = num // 100000, num % 100000
            if hundred_thousands == 1:
                result = self.NUMBERS[100000]
            else:
                result = self.number_to_words(hundred_thousands) + ' ' + self.NUMBERS[100000]
            return result if remainder == 0 else result + ' ' + self.number_to_words(remainder)
        
        if num < 1000000000:
            millions, remainder = num // 1000000, num % 1000000
            result = self.number_to_words(millions) + ' ' + self.NUMBERS[1000000]
            return result if remainder == 0 else result + ' ' + self.number_to_words(remainder)
        
        if num < 1000000000000:
            billions, remainder = num // 1000000000, num % 1000000000
            result = self.number_to_words(billions) + ' ' + self.NUMBERS[1000000000]
            return result if remainder == 0 else result + ' ' + self.number_to_words(remainder)
        
        trillions, remainder = num // 1000000000000, num % 1000000000000
        result = self.number_to_words(trillions) + ' ' + self.NUMBERS[1000000000000]
        return result if remainder == 0 else result + ' ' + self.number_to_words(remainder)
    
    def words_to_number(self, text):
        words = text.strip().lower().split()
        if len(words) == 1 and words[0] in self.WORD_TO_NUMBER:
            return self.WORD_TO_NUMBER[words[0]]
        
        total, current = 0, 0
        i = 0
        
        while i < len(words):
            word = words[i]
            
            if word == 'их' and i + 1 < len(words) and words[i + 1] == 'наяд':
                num = self.WORD_TO_NUMBER.get('их наяд', 1000000000000)
                total += (current if current > 0 else 1) * num
                current = 0
                i += 2
                continue
            
            if word not in self.WORD_TO_NUMBER:
                raise ValueError("Unknown word: {}".format(word))
            
            num = self.WORD_TO_NUMBER[word]
            
            if num >= 1000:
                total += (current if current > 0 else 1) * num
                current = 0
            elif num == 100:
                if current == 0:
                    current = 100
                else:
                    current *= num
            else:
                current += num
            
            i += 1
        
        return total + current
    
    def transliterate(self, text, to_script='cyrillic', trans_num=False):
        if to_script.lower() in ['cyrillic', 'cyr', 'c']:
            return self.latin_to_cyrillic(text, trans_num=trans_num)
        elif to_script.lower() in ['latin', 'lat', 'l']:
            return self.cyrillic_to_latin(text, trans_num=trans_num)
        raise ValueError("to_script must be 'cyrillic' or 'latin'")


_transliterator = MongolianTransliterator()

def latin_to_cyrillic(text, trans_num=False):
    return _transliterator.latin_to_cyrillic(text, trans_num=trans_num)

def cyrillic_to_latin(text, trans_num=False):
    return _transliterator.cyrillic_to_latin(text, trans_num=trans_num)

def number_to_words(num):
    return _transliterator.number_to_words(num)

def words_to_number(text):
    return _transliterator.words_to_number(text)

def transliterate(text, to_script='cyrillic', trans_num=False):
    return _transliterator.transliterate(text, to_script=to_script, trans_num=trans_num)
