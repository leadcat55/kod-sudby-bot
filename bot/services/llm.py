import httpx
from typing import Optional
from ..config import config
from ..services.numerology import numerology

# Описание входных данных для каждого типа расчёта
CALC_INPUT_DESCRIPTIONS = {
    "life_path": "📅 Использована **только дата рождения**",
    "soul": "👤 Использовано **только имя**",
    "personality": "👤 Использовано **только имя**",
    "destiny": "👤 Использовано **только имя**",
    "birthday": "📅 Использована **только дата рождения**",
}

CALC_TYPE_NAMES = {
    "life_path": "Число Жизненного Пути",
    "soul": "Число Души",
    "destiny": "Число Судьбы",
    "personality": "Число Личности",
    "birthday": "Число Дня Рождения",
}


class LLMService:
    def __init__(self):
        self.api_url = config.LLM_API_URL
        self.api_key = config.LLM_API_KEY
        self.model = config.LLM_MODEL
        print(f"[LLM] init: url={self.api_url}, key={'***' + self.api_key[-4:] if self.api_key else 'ПУСТО'}, model={self.model}", flush=True)

    def get_calc_input_description(self, calc_type: str, birth_date=None, full_name=None) -> str:
        """Return a human-readable description of which inputs are used for a calculation.

        For date-based calculations (life_path, birthday), shows the full
        digit-by-digit calculation breakdown when birth_date is provided.

        For name-based calculations (soul, personality, destiny), shows the
        letter-by-letter calculation breakdown when full_name is provided.
        """
        # Try to generate a calculation breakdown
        if birth_date is not None or full_name:
            breakdown = numerology.get_calc_breakdown(calc_type, birth_date, full_name or "")
            if breakdown:
                return breakdown

        # Fall back to generic descriptions
        return CALC_INPUT_DESCRIPTIONS.get(calc_type, "📅👤 Используются дата рождения и имя")

    def get_calc_type_name(self, calc_type: str) -> str:
        """Return a human-readable name for a calculation type"""
        return CALC_TYPE_NAMES.get(calc_type, calc_type)

    async def interpret_number(self, calc_type: str, number: int, birth_date, full_name: str) -> str:
        """Generate a short AI interpretation of a single numerology number"""
        input_desc = self.get_calc_input_description(calc_type, birth_date, full_name)
        type_name = self.get_calc_type_name(calc_type)

        if not self.api_key:
            return self._get_fallback_interpretation(calc_type, number, input_desc)

        prompt = (
            f"Ты — опытный нумеролог. Дай краткую, но содержательную расшифровку.\n\n"
            f"Человек: {full_name}, дата рождения: {birth_date}\n"
            f"Тип расчёта: {type_name}\n"
            f"Число: {number}\n\n"
            f"Напиши 3-5 предложений: что означает это число, "
            f"какие сильные стороны даёт, и один конкретный совет. "
            f"Без воды, по делу. Используй эзотерический стиль."
        )

        async with httpx.AsyncClient() as client:
            print(f"[LLM] запрос к {self.api_url}, модель={self.model}, ключ={'есть' if self.api_key else 'НЕТ'}", flush=True)
            try:
                response = await client.post(
                    self.api_url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 300,
                    },
                    timeout=30.0,
                )
                print(f"[LLM] статус: {response.status_code}", flush=True)
                if response.status_code == 200:
                    ai_text = response.json()["choices"][0]["message"]["content"]
                    return f"{input_desc}\n\n{ai_text}"
                else:
                    print(f"[LLM] ошибка: {response.text[:200]}", flush=True)
            except Exception as e:
                print(f"[LLM] исключение: {e}", flush=True)
        return self._get_fallback_interpretation(calc_type, number, input_desc)

    def _get_fallback_interpretation(self, calc_type: str, number: int, input_desc: str = "") -> str:
        interpretations = {
            "life_path": {
                1: "Число Пути 1 — ты лидер по натуре. Твоя сила в самостоятельности и решительности. Совет: доверяй своей интуиции при принятии решений.",
                2: "Число Пути 2 — ты дипломат и чувствуешь других людей. Твоя сила в эмпатии и умении объединять. Совет: не забывай о своих границах.",
                3: "Число Пути 3 — ты творческая натура с яркой энергией. Твоя сила в самовыражении и оптимизме. Совет: направь творчество в конкретное русло.",
                4: "Число Пути 4 — ты строитель и организатор. Твоя сила в надёжности и системности. Совет: не бойся мечтать смелее.",
                5: "Число Пути 5 — ты искатель приключений и свободы. Твоя сила в адаптивности и энергии. Совет: найди баланс между свободой и стабильностью.",
                6: "Число Пути 6 — ты опора для близких. Твоя сила в заботе и гармонии. Совет: учись принимать помощь от других.",
                7: "Число Пути 7 — ты мыслитель и философ. Твоя сила в глубине анализа и интуиции. Совет: не замыкайся в себе, делись открытиями.",
                8: "Число Пути 8 — ты амбициозный стратег. Твоя сила в целеустремлённости и умении управлять. Совет: помни о балансе материального и духовного.",
                9: "Число Пути 9 — ты гуманист с широким сердцем. Твоя сила в сострадании и мудрости. Совет: начни с малого — помоги одному человеку.",
                11: "Мастер-число 11 — ты несёшь высшую духовную миссию. Твоя сила в интуиции и вдохновении. Совет: доверяй внутреннему голосу.",
                22: "Мастер-число 22 — ты мастер-строитель, способен менять мир. Твоя сила в масштабном видении. Совет: начни реализовывать свои большие планы.",
                33: "Мастер-число 33 — ты учитель и целитель. Твоя сила в безусловной любви. Совет: делись мудростью, но не забывай о себе.",
            },
            "soul": {
                1: "Число Души 1 — глубинная потребность в лидерстве и самовыражении.",
                2: "Число Души 2 — потребность в гармонии и глубоких связях с людьми.",
                3: "Число Души 3 — потребность в творчестве и радости.",
                4: "Число Души 4 — потребность в стабильности и порядке.",
                5: "Число Души 5 — потребность в свободе и приключениях.",
                6: "Число Души 6 — потребность в любви и заботе о близких.",
                7: "Число Души 7 — потребность в познании и уединении.",
                8: "Число Души 8 — потребность в успехе и признании.",
                9: "Число Души 9 — потребность в служении и помощи другим.",
            },
            "destiny": {
                1: "Число Судьбы 1 — твоя миссия: стать лидером и первопроходцем.",
                2: "Число Судьбы 2 — твоя миссия: объединять и сглаживать конфликты.",
                3: "Число Судьбы 3 — твоя миссия: вдохновлять и радовать мир.",
                4: "Число Судьбы 4 — твоя миссия: строить прочные основы.",
                5: "Число Судьбы 5 — твоя миссия: нести перемены и свободу.",
                6: "Число Судьбы 6 — твоя миссия: создавать гармонию вокруг.",
                7: "Число Судьбы 7 — твоя миссия: искать истину и делиться мудростью.",
                8: "Число Судьбы 8 — твоя миссия: достигать высот успеха.",
                9: "Число Судьбы 9 — твоя миссия: служить человечеству.",
            },
        }

        calc_interps = interpretations.get(calc_type, {})
        result = calc_interps.get(number, f"Число {number} несёт в себе уникальную энергию, которая проявляется через твою личность.")
        if input_desc:
            return f"{input_desc}\n\n{result}"
        return result

    async def generate_deep_analysis(self, birth_date, full_name: str) -> Optional[str]:
        """Generate deep numerology analysis using LLM"""
        if not self.api_key:
            return self._get_fallback_analysis(birth_date, full_name)

        numbers = numerology.get_basic_numbers(birth_date, full_name)
        square = numerology.pythagorean_square(birth_date, full_name)

        prompt = f"""Составь подробный нумерологический анализ на основе данных:

Дата рождения: {birth_date}
Имя: {full_name}

Числа:
- Жизненный путь: {numbers['life_path']} (из даты рождения)
- Душа: {numbers['soul']} (из имени)
- Личность: {numbers['personality']} (из имени)
- Судьба: {numbers['destiny']} (из имени)
- День рождения: {numbers['birthday']} (из даты рождения)

Квадрат Пифагора:
- Первая линия: {square['first_line']} (из даты рождения)
- Вторая линия: {square['second_line']}
- Третья линия: {square['third_line']}
- Число имени: {square['name_value']} (из имени)

Составь развёрнутый анализ (минимум 1000 слов) с разделами:
1. Общая характеристика личности
2. Таланты и способности
3. Карьера и финансы
4. Отношения и любовь
5. Здоровье
6. Жизненные уроки
7. Рекомендации на текущий год
8. Совместимость с другими числами

Используй эзотерический стиль, но с конкретными рекомендациями."""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2000
                },
                timeout=60.0
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
        return None

    def _get_fallback_analysis(self, birth_date, full_name: str) -> str:
        """Fallback analysis without LLM"""
        numbers = numerology.get_basic_numbers(birth_date, full_name)
        square = numerology.pythagorean_square(birth_date, full_name)
        return f"""🔮 **Глубокий нумерологический анализ**

**Для:** {full_name}
**Дата рождения:** {birth_date}

---

**Как рассчитаны числа:**
- Жизненный путь: {numbers['life_path']} — из даты рождения
- Душа: {numbers['soul']} — из имени
- Личность: {numbers['personality']} — из имени
- Судьба: {numbers['destiny']} — из имени
- День рождения: {numbers['birthday']} — из даты рождения

**1. Общая характеристика**

Ваше Число Жизненного Пути — {numbers['life_path']}. Это определяет ваш основной жизненный сценарий и карьерные векторы.

**2. Таланты и способности**

Число Души {numbers['soul']} указывает на ваши глубинные таланты и внутренние желания.
Число Личности {numbers['personality']} показывает, как вас воспринимают окружающие.

**3. Карьера и финансы**

Число Судьбы {numbers['destiny']} определяет вашу судьбоносную миссию в этом мире.

**4. Отношения и любовь**

Ваши числа указывают на подход к отношениям и потребности в партнёрстве.

**5. Здоровье**

Обратите внимание на энергетические паттерны, связанные с вашими числами.

**6. Жизненные уроки**

Число Жизненного Пути {numbers['life_path']} несёт важный урок для вашего роста.

**7. Рекомендации**

Работайте с вашими сильными сторонами, основанными на числах {numbers['life_path']} и {numbers['soul']}.

**8. Квадрат Пифагора**

Первая линия: {square['first_line']}
Вторая линия: {square['second_line']}
Третья линия: {square['third_line']}
Число имени: {square['name_value']}

---

*Дисклеймер: Данный анализ носит развлекательный характер.*"""

    def fate_matrix_text(self, birth_date, full_name: str) -> str:
        """Generate Fate Matrix (Матрица Судьбы) text report"""
        matrix = numerology.fate_matrix(birth_date)
        numbers = numerology.get_basic_numbers(birth_date, full_name)

        lines = [
            "📊 **Матрица Судьбы (по Наталье Сидоровой)**",
            "",
            f"**Для:** {full_name}",
            f"**Дата рождения:** {birth_date}",
            "",
            "---",
            "",
            "**Расчёт четырёх ключевых чисел:**",
            f"• 1-е число (A): {matrix['a']} — сумма всех цифр даты рождения",
            f"• 2-е число (B): {matrix['b']} — сумма цифр 1-го числа (Число Жизненного Пути)",
            f"• 3-е число (C): {matrix['c']} — разность: |{matrix['digits'][0]} - ({len(str(matrix['a']))} × {matrix['digits'][0]})|",
            f"• 4-е число (D): {matrix['d']} — сумма цифр 3-го числа",
            "",
            "**Матрица 3×3:**",
            "",
            f"  {matrix['day']:>4}  |  {matrix['month']:>4}  |  {matrix['year']:>4}",
            f"  {matrix['a']:>4}  |  {matrix['b']:>4}  |  {matrix['c']:>4}",
            f"  {matrix['d']:>4}  |  {matrix['life_path']:>4}  |  {matrix['d']:>4}",
            "",
            "---",
            "",
            "**Значение ячеек:**",
        ]

        cell_labels = [
            ("День рождения", matrix['day']),
            ("Месяц рождения", matrix['month']),
            ("Год рождения", matrix['year']),
            ("1-е число (A)", matrix['a']),
            ("2-е число / Путь (B)", matrix['b']),
            ("3-е число (C)", matrix['c']),
            ("4-е число (D)", matrix['d']),
            ("Число Жизненного Пути", matrix['life_path']),
            ("4-е число (D)", matrix['d']),
        ]

        for i, (label, value) in enumerate(cell_labels, 1):
            meaning = matrix['cell_meanings'].get(i, "")
            lines.append(f"  {i}. **{label}** = {value} — {meaning}")

        lines.extend([
            "",
            "---",
            "",
            "**Интерпретация:**",
            "",
            f"• **Ячейка 1** (День рождения {matrix['day']}): Отражает ваше физическое тело, здоровье и силу. Чем выше число, тем больше энергии и активности вы проявляете в физической плоскости.",
            f"• **Ячейка 2** (Месяц {matrix['month']}): Связана с эмоциями, чувствами и отношениями с близкими. Показывает, как вы выражаете чувства и строите связи.",
            f"• **Ячейка 3** (Год {matrix['year']}): Отражает карьеру, публичную жизнь и социальный статус. Указывает на ваш путь в обществе и профессиональные достижения.",
            f"• **Ячейка 4** (Число A = {matrix['a']}): Ваши таланты, способности и творческие данные. Это то, что приходит естественно и может быть развито.",
            f"• **Ячейка 5** (Число B = {matrix['b']}): Главная цель жизни, смысл существования. Это ваша жизненная миссия, определяющая направление развития.",
            f"• **Ячейка 6** (Число C = {matrix['c']}): Препятствия и вызовы, с которыми вы столкнетесь. Показывает, что нужно преодолеть на пути к цели.",
            f"• **Ячейка 7** (Число D = {matrix['d']}): Прошлые жизни и кармические уроки. То, что вы переносите из прошлых воплощений.",
            f"• **Ячейка 8** (Путь = {matrix['life_path']}): Ваш основной жизненный путь и миссия. Ключевое число, определяющее характер и судьбоносные решения.",
            f"• **Ячейка 9** (Число D = {matrix['d']}): Наследство от прошлых жизней, то, что вы получаете по наследству. Дополняет ячейку 7.",
            "",
            "---",
            "",
            f"*Число Жизненного Пути: {numbers['life_path']}*",
            f"*Число Души: {numbers['soul']}*",
            f"*Число Судьбы: {numbers['destiny']}*",
            "",
            "*Дисклеймер: Данный анализ носит развлекательный характер.*",
        ])

        return "\n".join(lines)

    def pythagorean_square_text(self, birth_date, full_name: str) -> str:
        """Generate Pythagorean Square (Квадрат Пифагора) text report"""
        square = numerology.pythagorean_square(birth_date, full_name)
        numbers = numerology.get_basic_numbers(birth_date, full_name)

        lines = [
            "🔢 **Квадрат Пифагора**",
            "",
            f"**Для:** {full_name}",
            f"**Дата рождения:** {birth_date}",
            "",
            "---",
            "",
            "**Как рассчитан квадрат:**",
            f"• Первое доп. число: {square['first_line']} — сумма всех цифр даты рождения",
            f"• Второе доп. число: {square['second_line']} — сумма цифр первого числа",
            f"• Третье доп. число: {square['third_line']} — первое число - (2 × первая цифра даты)",
            f"• Четвёртое доп. число: {square['fourth_line']} — сумма цифр третьего числа",
            f"• Число имени: {square['name_value']} — число судьбы (из имени)",
            "",
            "**Все цифры вместе:**",
            f"  {square['first_line']} + {square['second_line']} + {square['third_line']} + {square['fourth_line']} + [{square['name_value']}]",
            "",
            "---",
            "",
            "**Расшифровка квадрата (количество клеток для каждой цифры 1-9):**",
            "",
        ]

        for num in range(1, 10):
            count = square['counts'][num]
            if count > 0:
                cell_word = "клетка" if count == 1 else ("клеты" if count < 5 else "клеток")
                lines.append(f"  • **Число {num}**: {count} {cell_word}")
            else:
                lines.append(f"  • **Число {num}**: 0 (нет клеток)")

        lines.extend([
            "",
            "---",
            "",
            "**Интерпретация чисел:**",
            "",
            "• **Число 1** (1 клетка): Самостоятельность, инициатива, лидерство. Чем больше клеток — тем сильнее природный лидер.",
            "• **Число 2** (2 клетки): Эмоциональная устойчивость, дипломатия, способность к партнёрству. Отражает чувствительность.",
            "• **Число 3** (3 клетки): Творческие способности, коммуникабельность, оптимизм. Чем больше — тем ярче творчество.",
            "• **Число 4** (4 клетки): Системность, дисциплина, порядок. Отражает способность строить основы и работать сдержанно.",
            "• **Число 5** (5 клеток): Свобода, приключения, адаптивность. Чем больше — тем сильнее потребность в переменах.",
            "• **Число 6** (6 клеток): Забота о близких, ответственность, гармония. Отражает способность любить и заботиться.",
            "• **Число 7** (7 клеток): Интуиция, философия, духовность. Чем больше — тем глже мыслительные способности.",
            "• **Число 8** (8 клеток): Амбиции, власть, материальный успех. Отражает способность к лидерству и достижениям.",
            "• **Число 9** (9 клеток): Человекочувствие, гуманизм, мудрость. Чем больше — тем сильнее чувство долга перед людьми.",
            "",
            "---",
            "",
            f"*Число Жизненного Пути: {numbers['life_path']}*",
            f"*Число Души: {numbers['soul']}*",
            f"*Число Судьбы: {numbers['destiny']}*",
            f"*Число Личности: {numbers['personality']}*",
            f"*Число Дня Рождения: {numbers['birthday']}*",
            "",
            "*Дисклеймер: Данный анализ носит развлекательный характер.*",
        ])

        return "\n".join(lines)

    def _get_fallback_fate_matrix(self, birth_date, full_name: str) -> str:
        """Fallback Fate Matrix text without LLM"""
        return self.fate_matrix_text(birth_date, full_name)

    def _get_fallback_pythagorean_square(self, birth_date, full_name: str) -> str:
        """Fallback Pythagorean Square text without LLM"""
        return self.pythagorean_square_text(birth_date, full_name)

llm = LLMService()


