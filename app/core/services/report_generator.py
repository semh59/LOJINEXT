import io
import os
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        Image,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from app.config import get_system_font
from app.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


class PDFReportGenerator:
    """
    Elite PDF Rapor Motoru (ReportLab tabanlı)

    Özellikler:
    - %100 Türkçe Karakter Desteği (TrueType)
    - Kurumsal Premium Tasarım (Modern Palette)
    - Dinamik Tablo ve Grafik Alanları
    """

    # Kurumsal Renk Paleti (ReportLab varsa HexColor, yoksa string)
    PRIMARY = None
    SECONDARY = None
    SUCCESS = None
    WARNING = None
    DANGER = None
    BG_LIGHT = None
    TEXT_DARK = None

    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            logger.error("reportlab kütüphanesi yüklü değil, PDF üretimi yapılamaz!")
            return

        # Renkleri burada ata (HexColor'ın import kontrolü geçmiş olduğu garanti)
        from reportlab.lib.colors import HexColor

        PDFReportGenerator.PRIMARY = HexColor("#1e40af")  # Indigo 800
        PDFReportGenerator.SECONDARY = HexColor("#64748b")  # Slate 500
        PDFReportGenerator.SUCCESS = HexColor("#059669")  # Emerald 600
        PDFReportGenerator.WARNING = HexColor("#d97706")  # Amber 600
        PDFReportGenerator.DANGER = HexColor("#dc2626")  # Red 600
        PDFReportGenerator.BG_LIGHT = HexColor("#f8fafc")  # Slate 50
        PDFReportGenerator.TEXT_DARK = HexColor("#0f172a")  # Slate 900

        self._register_fonts()
        self._styles = None

    def _register_fonts(self):
        """Türkçe karakterler için font kaydı"""
        try:
            # 1. Öncelik: Proje içindeki gömülü fontlar (Taşınabilirlik için)
            current_dir = os.path.dirname(
                os.path.abspath(__file__)
            )  # app/core/services
            app_dir = os.path.dirname(os.path.dirname(current_dir))  # app
            asset_font = os.path.join(app_dir, "assets", "fonts", "EliteFont.ttf")
            asset_font_bold = os.path.join(
                app_dir, "assets", "fonts", "EliteFont-Bold.ttf"
            )

            if os.path.exists(asset_font):
                pdfmetrics.registerFont(TTFont("EliteFont", asset_font))
                pdfmetrics.registerFont(
                    TTFont(
                        "EliteFontBold",
                        asset_font_bold
                        if os.path.exists(asset_font_bold)
                        else asset_font,
                    )
                )
                self.font_name = "EliteFont"
                self.font_bold = "EliteFontBold"
                logger.info("Gömülü fontlar başarıyla yüklendi.")
                return

            # 2. Öncelik: Sistem fontları
            font_path = get_system_font()
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont("EliteFont", font_path))
                pdfmetrics.registerFont(
                    TTFont(
                        "EliteFontBold",
                        font_path.replace(".ttf", "bd.ttf")
                        if "bd.ttf" not in font_path
                        else font_path,
                    )
                )
                self.font_name = "EliteFont"
                self.font_bold = "EliteFontBold"
            else:
                self.font_name = "Helvetica"
                self.font_bold = "Helvetica-Bold"
        except Exception as e:
            logger.warning(f"Font kaydı yapılamadı: {e}. Standart font kullanılacak.")
            self.font_name = "Helvetica"
            self.font_bold = "Helvetica-Bold"

    @property
    def styles(self):
        if self._styles is None and REPORTLAB_AVAILABLE:
            self._styles = getSampleStyleSheet()
            # Elite Styles
            self._styles.add(
                ParagraphStyle(
                    name="EliteTitle",
                    parent=self._styles["Heading1"],
                    fontName=self.font_bold,
                    fontSize=22,
                    textColor=self.PRIMARY,
                    spaceAfter=20,
                    alignment=1,  # Center
                )
            )
            self._styles.add(
                ParagraphStyle(
                    name="EliteSection",
                    parent=self._styles["Heading2"],
                    fontName=self.font_bold,
                    fontSize=14,
                    textColor=self.SECONDARY,
                    spaceBefore=15,
                    spaceAfter=10,
                    borderPadding=(0, 0, 5, 0),
                    borderWidth=0,
                    borderColor=self.PRIMARY,  # Bottom border simulated via styling if needed
                )
            )
            self._styles.add(
                ParagraphStyle(
                    name="EliteBody",
                    parent=self._styles["Normal"],
                    fontName=self.font_name,
                    fontSize=10,
                    textColor=self.TEXT_DARK,
                    leading=14,
                )
            )
            self._styles.add(
                ParagraphStyle(
                    name="EliteFooter",
                    parent=self._styles["Normal"],
                    fontName=self.font_name,
                    fontSize=8,
                    textColor=self.SECONDARY,
                    alignment=1,  # Center
                )
            )
        return self._styles

    def _create_header(
        self, elements: List, title: str, subtitle: Optional[str] = None
    ):
        """Rapor başlığı oluştur"""
        elements.append(Paragraph(title.upper(), self.styles["EliteTitle"]))
        if subtitle:
            elements.append(Paragraph(subtitle, self.styles["EliteBody"]))
        elements.append(Spacer(1, 0.8 * cm))

    def _create_metric_box(self, label: str, value: str, color: Any = None) -> Table:
        """Dashboard tipi metrik kutusu"""
        data = [
            [
                Paragraph(f"<b>{label}</b>", self.styles["EliteBody"]),
                Paragraph(
                    f"<font color='{color.hexval() if color else '#000000'}'>{value}</font>",
                    self.styles["EliteBody"],
                ),
            ]
        ]
        t = Table(data, colWidths=[4 * cm, 4 * cm])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), self.BG_LIGHT),
                    ("BOX", (0, 0), (-1, -1), 1, self.SECONDARY),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        return t

    def generate_fleet_summary(
        self, start_date: date, end_date: date, data: Dict
    ) -> bytes:
        """Elite Filo Özet Raporu"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )
        elements = []

        # 1. Header
        self._create_header(
            elements,
            "Filo Performans Raporu",
            f"Sefer Dönemi: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}",
        )

        # 2. Özet Metrikler (2x3 Grid)
        elements.append(Paragraph("GENEL ÖZET", self.styles["EliteSection"]))
        m_data = [
            [
                self._create_metric_box(
                    "Toplam Araç", str(data.get("total_vehicles", 0))
                ),
                self._create_metric_box(
                    "Toplam Sefer", str(data.get("total_trips", 0))
                ),
            ],
            [
                self._create_metric_box(
                    "Toplam Mesafe", f"{data.get('total_distance', 0):,.0f} km"
                ),
                self._create_metric_box(
                    "Yakıt Tüketimi", f"{data.get('total_fuel', 0):,.0f} L"
                ),
            ],
            [
                self._create_metric_box(
                    "Ort. Tüketim",
                    f"{data.get('avg_consumption', 0):.2f} L/100km",
                    self.SUCCESS,
                ),
                self._create_metric_box(
                    "Toplam Maliyet",
                    f"{data.get('total_cost', 0):,.2f} TL",
                    self.PRIMARY,
                ),
            ],
        ]
        metrics_grid = Table(m_data, colWidths=[8.5 * cm, 8.5 * cm])
        metrics_grid.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        elements.append(metrics_grid)
        elements.append(Spacer(1, 1 * cm))

        # 3. Araç Performans Tablosu
        if data.get("vehicle_performance"):
            elements.append(Paragraph("ARAÇ BAZLI ANALİZ", self.styles["EliteSection"]))
            v_data = [["Plaka", "Sefer", "KM", "Tüketim", "Puan", "Durum"]]
            for v in data["vehicle_performance"][:15]:
                puan = v.get("performance_score", 0)
                status = "KRİTİK" if puan < 50 else "İYİ" if puan > 80 else "NORMAL"
                v_data.append(
                    [
                        v.get("plaka", "-"),
                        str(v.get("trips", 0)),
                        f"{v.get('distance', 0):,.0f}",
                        f"{v.get('consumption', 0):.2f}",
                        f"{puan:.1f}",
                        status,
                    ]
                )

            v_table = Table(
                v_data, colWidths=[3 * cm, 2 * cm, 3 * cm, 4 * cm, 2 * cm, 3 * cm]
            )
            v_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), self.PRIMARY),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), self.font_bold),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, self.BG_LIGHT],
                        ),
                        ("GRID", (0, 0), (-1, -1), 0.5, self.SECONDARY),
                    ]
                )
            )
            elements.append(v_table)

        # 4. Footer
        elements.append(Spacer(1, 2 * cm))
        elements.append(
            Paragraph(
                f"LojiNext AI Zekası Tarafından {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M')} tarihinde oluşturulmuştur.",
                self.styles["EliteFooter"],
            )
        )

        doc.build(elements)
        return buffer.getvalue()

    def generate_vehicle_report(
        self, arac_id: int, month: int, year: int, data: Dict
    ) -> bytes:
        """Elite Araç Detay Raporu"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []

        plaka = data.get("plaka", f"#{arac_id}")
        self._create_header(
            elements,
            f"ARAÇ ANALİZ DOSYASI: {plaka}",
            f"Rapor Dönemi: {month:02d}/{year}",
        )

        # Teknik Bilgiler Kartı
        elements.append(Paragraph("TEKNİK ÖZELLİKLER", self.styles["EliteSection"]))
        tech_data = [
            ["Marka / Model", f"{data.get('marka', '-')} {data.get('model', '')}"],
            ["Hedef Tüketim", f"{data.get('hedef_tuketim', 32.0):.1f} L/100km"],
            ["Performans Skoru", f"{data.get('performance_score', 0):.1f} / 100"],
        ]
        t_table = Table(tech_data, colWidths=[6 * cm, 10 * cm])
        t_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), self.BG_LIGHT),
                    ("GRID", (0, 0), (-1, -1), 0.5, self.SECONDARY),
                ]
            )
        )
        elements.append(t_table)

        # ... Diğer bölümler benzer elite tasarım ile eklenebilir ...

        doc.build(elements)
        return buffer.getvalue()

    async def async_generate_fleet_summary(
        self, start_date: date, end_date: date, data: Dict
    ) -> bytes:
        """Asenkron wrapper: Filo Özet Raporu"""
        import asyncio

        return await asyncio.to_thread(
            self.generate_fleet_summary, start_date, end_date, data
        )

    async def async_generate_vehicle_report(
        self, arac_id: int, month: int, year: int, data: Dict
    ) -> bytes:
        """Asenkron wrapper: Araç Detay Raporu"""
        import asyncio

        return await asyncio.to_thread(
            self.generate_vehicle_report, arac_id, month, year, data
        )


# Thread-safe Singleton
import threading

_report_generator: Optional[PDFReportGenerator] = None
_report_generator_lock = threading.Lock()


def get_report_generator() -> PDFReportGenerator:
    """Thread-safe singleton getter"""
    global _report_generator
    if _report_generator is None:
        with _report_generator_lock:
            if _report_generator is None:
                _report_generator = PDFReportGenerator()
    return _report_generator
