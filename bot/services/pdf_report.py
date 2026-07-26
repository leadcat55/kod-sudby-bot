from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import date
import os

from .numerology import numerology
from ..models.user import User

# Register Cyrillic font
FONT_PATH = os.path.join(os.environ.get("SYSTEMROOT", "C:\\Windows"), "Fonts", "arial.ttf")
if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont('Arial', FONT_PATH))
    DEFAULT_FONT = 'Arial'
else:
    DEFAULT_FONT = 'Helvetica'

class PDFReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name='TitleCustom',
            parent=self.styles['Title'],
            fontName=DEFAULT_FONT,
            fontSize=24,
            textColor=HexColor('#6B46C1'),
            spaceAfter=20
        ))
        self.styles.add(ParagraphStyle(
            name='SubtitleCustom',
            parent=self.styles['Heading2'],
            fontName=DEFAULT_FONT,
            fontSize=16,
            textColor=HexColor('#4A5568'),
            spaceAfter=12
        ))
        # Update all styles to use the font
        for style in self.styles.byName.values():
            if hasattr(style, 'fontName'):
                style.fontName = DEFAULT_FONT
    
    def generate_basic_report(self, user: User, output_path: str) -> str:
        """Generate basic PDF report (5+ pages)"""
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        
        birth_date = date.fromisoformat(user.birth_date) if isinstance(user.birth_date, str) else user.birth_date
        numbers = numerology.get_basic_numbers(birth_date, user.full_name)
        square = numerology.pythagorean_square(birth_date, user.full_name)
        
        # Title page
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph("КОД СУДЬБЫ", self.styles['TitleCustom']))
        story.append(Paragraph(f"Персональный нумерологический отчёт", self.styles['SubtitleCustom']))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(f"Дата рождения: {birth_date.strftime('%d.%m.%Y')}", self.styles['Normal']))
        story.append(Paragraph(f"Имя: {user.full_name}", self.styles['Normal']))
        story.append(Spacer(1, 1*inch))
        story.append(Paragraph("Дисклеймер: Данный отчёт носит исключительно развлекательный характер и не является научной консультацией.", self.styles['Normal']))
        
        # Life Path Number
        story.append(PageBreak())
        story.append(Paragraph("Число Жизненного Пути", self.styles['Heading1']))
        story.append(Paragraph(str(numbers['life_path']), self.styles['TitleCustom']))
        story.append(Paragraph(self._get_life_path_full_description(numbers['life_path']), self.styles['Normal']))
        
        # Soul Number
        story.append(PageBreak())
        story.append(Paragraph("Число Души", self.styles['Heading1']))
        story.append(Paragraph(str(numbers['soul']), self.styles['TitleCustom']))
        story.append(Paragraph(self._get_soul_full_description(numbers['soul']), self.styles['Normal']))
        
        # Personality Number
        story.append(PageBreak())
        story.append(Paragraph("Число Личности", self.styles['Heading1']))
        story.append(Paragraph(str(numbers['personality']), self.styles['TitleCustom']))
        story.append(Paragraph(self._get_personality_full_description(numbers['personality']), self.styles['Normal']))
        
        # Destiny Number
        story.append(PageBreak())
        story.append(Paragraph("Число Судьбы", self.styles['Heading1']))
        story.append(Paragraph(str(numbers['destiny']), self.styles['TitleCustom']))
        story.append(Paragraph(self._get_destiny_full_description(numbers['destiny']), self.styles['Normal']))
        
        # Pythagorean Square
        story.append(PageBreak())
        story.append(Paragraph("Квадрат Пифагора", self.styles['Heading1']))
        story.append(Paragraph(f"Первая линия: {square['first_line']}", self.styles['Normal']))
        story.append(Paragraph(f"Вторая линия: {square['second_line']}", self.styles['Normal']))
        story.append(Paragraph(f"Третья линия: {square['third_line']}", self.styles['Normal']))
        story.append(Paragraph(f"Число имени: {square['name_value']}", self.styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("Расшифровка квадрата:", self.styles['Heading2']))
        for num, count in square['counts'].items():
            if count > 0:
                story.append(Paragraph(f"Число {num}: {count} {'клетка' if count == 1 else 'клетки' if count < 5 else 'клеток'}", self.styles['Normal']))
        
        doc.build(story)
        return output_path
    
    def _get_life_path_full_description(self, number: int) -> str:
        descriptions = {
            1: """Число Жизненного Пути 1 указывает на прирождённого лидера. Вы обладаете сильной волей, решительностью и стремлением к независимости.

**Таланты:** Предпринимательство, инициатива, смелость, оригинальность мышления.

**Карьера:** Вам подходят руководящие должности, собственный бизнес, творческие профессии, где нужна самостоятельность.

**Отношения:** Вы цените свободу, но способны на глубокую преданность. Ищете равноправного партнёра.

**Советы:** Учитесь слушать других, избегайте упрямства. Ваш потенциал огромен, но раскрывается через сотрудничество.""",
            2: """Число Жизненного Пути 2 символизирует партнёрство и гармонию. Вы — прирождённый дипломат и миротворец.

**Таланты:** Эмпатия, интуиция, способность сглаживать конфликты, тонкое понимание людей.

**Карьера:** Психология, медиация, HR, искусство, любая работа с людьми.

**Отношения:** Вы создаете глубокие эмоциональные связи. Главное — не терять себя в заботе о других.

**Советы:** Научитесь говорить «нет». Ваша чувствительность — дар, но требует защиты.""",
        }
        return descriptions.get(number, f"Число {number} несёт в себе уникальную энергию, которая определяет ваш жизненный путь.")
    
    def _get_soul_full_description(self, number: int) -> str:
        return f"Число Души {number} раскрывает ваши глубинные желания и внутренний мир..."
    
    def _get_personality_full_description(self, number: int) -> str:
        return f"Число Личности {number} показывает, как вас воспринимают окружающие..."
    
    def _get_destiny_full_description(self, number: int) -> str:
        return f"Число Судьбы {number} определяет ваше предназначение в этом мире..."

pdf_generator = PDFReportGenerator()
