from datetime import date
from typing import Dict, List, Tuple

class NumerologyEngine:
    """Core numerology calculation engine"""
    
    # Letter-to-number mapping (Pythagorean)
    LETTER_VALUES = {
        'а': 1, 'б': 2, 'в': 3, 'г': 4, 'д': 5, 'е': 6, 'ё': 7,
        'ж': 8, 'з': 9, 'и': 1, 'й': 2, 'к': 3, 'л': 4, 'м': 5,
        'н': 6, 'о': 7, 'п': 8, 'р': 9, 'с': 1, 'т': 2, 'у': 3,
        'ф': 4, 'х': 5, 'ц': 6, 'ч': 7, 'ш': 8, 'щ': 9, 'ъ': 1,
        'ы': 2, 'ь': 3, 'э': 4, 'ю': 5, 'я': 6
    }

    
    @staticmethod
    def reduce_to_single(n: int) -> int:
        """Reduce number to single digit (except master numbers 11, 22, 33)"""
        while n > 9 and n not in (11, 22, 33):
            n = sum(int(d) for d in str(n))
        return n
    
    @staticmethod
    def reduce_to_single_strict(n: int) -> int:
        """Strict reduction - always to single digit"""
        while n > 9:
            n = sum(int(d) for d in str(n))
        return n
    
    def life_path_number(self, birth_date: date) -> int:
        """Число Жизненного Пути - сумма всех цифр даты рождения"""
        date_str = birth_date.strftime("%d%m%Y")
        total = sum(int(d) for d in date_str)
        return self.reduce_to_single(total)
    
    def soul_number(self, full_name: str) -> int:
        """Число Души - сумма гласных букв полного имени"""
        vowels = set('аеёиоуыэюя')
        total = sum(
            self.LETTER_VALUES.get(c, 0) 
            for c in full_name.lower() 
            if c in vowels
        )
        return self.reduce_to_single(total)
    
    def personality_number(self, full_name: str) -> int:
        """Число Личности - сумма согласных букв полного имени"""
        vowels = set('аеёиоуыэюя')
        total = sum(
            self.LETTER_VALUES.get(c, 0) 
            for c in full_name.lower() 
            if c.isalpha() and c not in vowels
        )
        return self.reduce_to_single(total)
    
    def destiny_number(self, full_name: str) -> int:
        """Число Судьбы - сумма всех букв полного имени"""
        total = sum(
            self.LETTER_VALUES.get(c, 0) 
            for c in full_name.lower() 
            if c.isalpha()
        )
        return self.reduce_to_single(total)
    
    def birthday_number(self, birth_date: date) -> int:
        """Число Дня Рождения - день рождения"""
        return self.reduce_to_single(birth_date.day)
    
    def get_calc_breakdown(self, calc_type: str, birth_date: date = None, full_name: str = "") -> str:
        """Generate a human-readable calculation breakdown for a given calc type.
        
        For date-based calculations (life_path, birthday), shows the full
        digit-by-digit calculation, e.g.:
            14.09.1965 → 1+4+0+9+1+9+6+5 = 35 → 3+5 = 8
        
        For name-based calculations (soul, personality, destiny), shows the
        letter-by-letter calculation, e.g.:
            Иван → И(1) + а(1) = 2
        
        Returns None for unknown calc types or when required inputs are missing.
        """
        if calc_type == "life_path" and birth_date is not None:
            date_display = birth_date.strftime("%d.%m.%Y")
            date_str = birth_date.strftime("%d%m%Y")
            digits = [int(d) for d in date_str]
            total = sum(digits)
            digits_str = "+".join(str(d) for d in digits)

            # Build reduction steps (stop at master numbers 11, 22, 33)
            parts = []
            current = total
            while current > 9 and current not in (11, 22, 33):
                digit_parts = [int(d) for d in str(current)]
                step_sum = sum(digit_parts)
                parts.append(f"{'+'.join(str(p) for p in digit_parts)} = {step_sum}")
                current = step_sum

            if parts:
                return f"{date_display} → {digits_str} = {total} → {' → '.join(parts)}"
            else:
                return f"{date_display} → {digits_str} = {total}"

        elif calc_type == "birthday" and birth_date is not None:
            day = birth_date.day
            digits = [int(d) for d in str(day)]
            total = sum(digits)
            digits_str = "+".join(str(d) for d in digits)

            if total > 9:
                digit_parts = [int(d) for d in str(total)]
                step_str = "+".join(str(p) for p in digit_parts)
                return f"День {day} → {digits_str} = {total} → {step_str} = {sum(digit_parts)}"
            else:
                return f"День {day} → {digits_str} = {total}"

        elif calc_type in ("soul", "personality", "destiny") and full_name:
            vowels = set('аеёиоуыэюя')

            if calc_type == "soul":
                letters = [c for c in full_name if c.lower() in vowels and c.isalpha()]
            elif calc_type == "personality":
                letters = [c for c in full_name if c.isalpha() and c.lower() not in vowels]
            else:  # destiny
                letters = [c for c in full_name if c.isalpha()]

            if not letters:
                return None

            values = [self.LETTER_VALUES.get(c.lower(), 0) for c in letters]
            total = sum(values)

            # Build the display
            letter_values_str = " + ".join(f"{c}({v})" for c, v in zip(letters, values))

            # Build reduction steps (stop at master numbers 11, 22, 33)
            parts = []
            current = total
            while current > 9 and current not in (11, 22, 33):
                digit_parts = [int(d) for d in str(current)]
                step_sum = sum(digit_parts)
                parts.append(f"{'+'.join(str(p) for p in digit_parts)} = {step_sum}")
                current = step_sum

            if parts:
                return f"{full_name} → {letter_values_str} = {total} → {' → '.join(parts)}"
            else:
                return f"{full_name} → {letter_values_str} = {total}"

        return None

    def get_basic_numbers(self, birth_date: date, full_name: str) -> Dict[str, int]:
        """Get all basic numerology numbers"""
        return {
            "life_path": self.life_path_number(birth_date),
            "soul": self.soul_number(full_name),
            "personality": self.personality_number(full_name),
            "destiny": self.destiny_number(full_name),
            "birthday": self.birthday_number(birth_date)
        }
    
    def pythagorean_square(self, birth_date: date, full_name: str) -> Dict[str, List[int]]:
        """Calculate Pythagorean Square (Квадрат Пифагора) per methodical guide.
        
        Steps:
        1. First additional number: sum of all 8 digits of DDMMYYYY
        2. Second additional number: sum of digits of first number
        3. Third additional number: first_number - (2 × first_nonzero_digit_of_date)
        4. Fourth additional number: sum of digits of third number
        
        Zero is not included in the square.
        """
        # Get birth date digits
        date_digits = [int(d) for d in birth_date.strftime("%d%m%Y")]
        
        # Get name value
        name_value = self.destiny_number(full_name)
        name_digits = [int(d) for d in str(name_value)] if name_value > 9 else [name_value]
        
        # First additional number: sum of all date digits
        first_sum = sum(date_digits)
        first_line = date_digits
        
        # Second additional number: sum of digits of first number
        second_line = [int(d) for d in str(first_sum)] if first_sum > 9 else [first_sum]
        
        # Third additional number: first_number - (2 × first_nonzero_digit_of_date)
        # "if the first digit of the date is '0', the first non-zero digit is taken"
        first_nonzero = next((d for d in date_digits if d > 0), date_digits[0])
        third_value = first_sum - (2 * first_nonzero)
        if third_value < 0:
            third_value = abs(third_value)
        if third_value == 0:
            third_value = first_nonzero  # fallback
        third_line = [int(d) for d in str(third_value)] if third_value > 9 else [third_value]
        
        # Fourth additional number: sum of digits of third number
        fourth_value = self.reduce_to_single(third_value)
        fourth_line = [int(d) for d in str(fourth_value)] if fourth_value > 9 else [fourth_value]
        
        # All digits together (for counting)
        all_digits = first_line + second_line + third_line + fourth_line + name_digits
        
        # Count occurrences of each number (1-9), zero is not included
        counts = {i: all_digits.count(i) for i in range(1, 10)}
        
        return {
            "first_line": first_line,
            "second_line": second_line,
            "third_line": third_line,
            "fourth_line": fourth_line,
            "fourth_value": fourth_value,
            "name_value": name_value,
            "counts": counts
        }

    
    def fate_matrix(self, birth_date: date) -> Dict:
        """Calculate Fate Matrix (Матрица Судьбы) by Natalia Sidorova.
        
        The Matrix of Fate is a 3×3 grid based on the birth date.
        It uses four key numbers derived from the date of birth:
        
        - A (1st number): Sum of all 8 digits of DDMMYYYY
        - B (2nd number): Sum of digits of A (equals Life Path number)
        - C (3rd number): |first_digit - (num_digits_in_A × first_digit)|
        - D (4th number): Sum of digits of C
        
        The 3×3 matrix:
            [DD]  [MM]  [YYYY]
            [A]   [B]   [C]
            [D]   [LP]  [D]
        
        Where LP is the Life Path number.
        """
        date_str = birth_date.strftime("%d%m%Y")
        digits = [int(d) for d in date_str]
        
        day = birth_date.day
        month = birth_date.month
        year = birth_date.year
        
        # 1st number: sum of all 8 digits
        a = sum(digits)
        
        # 2nd number: sum of digits of A (equals Life Path)
        b = self.reduce_to_single(a)
        
        # 3rd number: |first_digit - (num_digits_in_A × first_digit)|
        first_digit = digits[0]
        num_digits_a = len(str(a))
        c = abs(first_digit - (num_digits_a * first_digit))
        if c == 0:
            c = first_digit  # fallback if difference is zero
        
        # 4th number: sum of digits of C
        d = self.reduce_to_single(c)
        
        # Life Path number
        life_path = self.life_path_number(birth_date)
        
        # Build the 3×3 matrix
        matrix = [
            [day, month, year],
            [a, b, c],
            [d, life_path, d]
        ]
        
        # Cell meanings (1-9)
        cell_meanings = {
            1: "Тело, здоровье, физическая сила",
            2: "Эмоции, чувства, отношения с близкими",
            3: "Карьера, публичная жизнь, социальный статус",
            4: "Таланты, способности, творческие способности",
            5: "Цель жизни, главное предназначение, смысл",
            6: "Препятствия, вызовы, то, что нужно преодолеть",
            7: "Прошлые жизни, кармические уроки",
            8: "Жизненный путь, основная миссия",
            9: "Наследство, наследство от прошлых жизней"
        }
        
        return {
            "day": day,
            "month": month,
            "year": year,
            "a": a,
            "b": b,
            "c": c,
            "d": d,
            "life_path": life_path,
            "matrix": matrix,
            "cell_meanings": cell_meanings,
            "date_str": date_str,
            "digits": digits,
        }
    
    def compatibility(self, birth1: date, name1: str, birth2: date, name2: str) -> Dict:
        """Calculate compatibility between two people"""
        numbers1 = self.get_basic_numbers(birth1, name1)
        numbers2 = self.get_basic_numbers(birth2, name2)
        
        # Simple compatibility score based on life path numbers
        diff = abs(numbers1["life_path"] - numbers2["life_path"])
        if diff == 0:
            score = 100
        elif diff <= 2:
            score = 85
        elif diff <= 4:
            score = 70
        elif diff <= 6:
            score = 55
        else:
            score = 40
        
        return {
            "person1": numbers1,
            "person2": numbers2,
            "compatibility_score": score,
            "description": self._get_compatibility_description(score)
        }
    
    def _get_compatibility_description(self, score: int) -> str:
        if score >= 90:
            return "Идеальная совместимость! Вы прекрасно дополняете друг друга."
        elif score >= 75:
            return "Хорошая совместимость. Есть потенциал для глубоких отношений."
        elif score >= 60:
            return "Средняя совместимость. Нужны усилия обоих партнёров."
        else:
            return "Сложная совместимость. Но это не преграда для любви!"

numerology = NumerologyEngine()
