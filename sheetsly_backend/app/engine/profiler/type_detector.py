"""Data type and semantic role detector for spreadsheet cells and column vectors."""

import re
from datetime import date, datetime
from typing import Any, List, Optional, Tuple

from app.models.schemas import DataTypeEnum, SemanticTypeEnum

# Regex patterns for type parsing
RE_INTEGER = re.compile(r"^[+-]?\d+$")
RE_FLOAT = re.compile(r"^[+-]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?$")
RE_CURRENCY = re.compile(
    r"^(?:Rp\.?|IDR|\$|€|£|¥)\s*[-+]?(?:\d{1,3}(?:[,\.]\d{3})*|\d+)(?:[,\.]\d+)?$|"
    r"^[-+]?(?:\d{1,3}(?:[,\.]\d{3})*|\d+)(?:[,\.]\d+)?\s*(?:Rp\.?|IDR|\$|€|£|¥)$",
    re.IGNORECASE,
)
RE_PERCENTAGE = re.compile(r"^[+-]?(?:\d{1,3}(?:[,\.]\d{3})*|\d+)(?:[,\.]\d+)?\s*%$")
RE_BOOLEAN = re.compile(r"^(?:true|false|yes|no|ya|tidak|t|f|y|n)$", re.IGNORECASE)

DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%m-%d-%Y",
    "%Y-%m-%d %H:%M:%S",
    "%d/%m/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M:%S",
    "%d-%b-%Y",
    "%d-%B-%Y",
    "%b-%y",
    "%B %Y",
]

IDENTIFIER_KEYWORDS = {"id", "code", "kode", "sku", "key", "no", "nomor", "nip", "nik", "uuid", "guid", "ref"}
TEMPORAL_KEYWORDS = {
    "date", "tanggal", "tgl", "time", "waktu", "year", "tahun", "thn", "month", "bulan", "bln",
    "day", "hari", "quarter", "kuartal", "period", "periode", "created_at", "updated_at"
}
MEASURE_KEYWORDS = {
    "revenue", "sales", "penjualan", "pendapatan", "omset", "omzet", "profit", "laba", "keuntungan",
    "cost", "biaya", "pengeluaran", "expense", "price", "harga", "total", "subtotal", "amount",
    "jumlah", "qty", "quantity", "kuantitas", "volume", "unit", "discount", "diskon", "tax", "pajak",
    "salary", "gaji", "score", "nilai", "rate", "kurs"
}
CATEGORICAL_KEYWORDS = {
    "category", "kategori", "type", "tipe", "jenis", "status", "region", "wilayah", "area",
    "city", "kota", "province", "provinsi", "country", "negara", "branch", "cabang",
    "product", "produk", "item", "customer", "pelanggan", "vendor", "supplier", "department", "departemen",
    "channel", "saluran", "payment_method", "metode_pembayaran", "gender", "kelamin"
}


class TypeDetector:
    """Deterministic data type and semantic role detector."""

    @classmethod
    def detect_value_type(cls, val: Any) -> Tuple[DataTypeEnum, Optional[Any]]:
        """
        Infers physical DataTypeEnum and returns parsed value representation.
        Returns: (DataTypeEnum, parsed_value)
        """
        if val is None:
            return DataTypeEnum.NULL, None

        if isinstance(val, bool):
            return DataTypeEnum.BOOLEAN, val

        if isinstance(val, (datetime, date)):
            return (DataTypeEnum.DATETIME if isinstance(val, datetime) else DataTypeEnum.DATE), val.isoformat()

        if isinstance(val, int):
            return DataTypeEnum.INTEGER, val

        if isinstance(val, float):
            return DataTypeEnum.FLOAT, val

        str_val = str(val).strip()
        if str_val == "" or str_val.lower() in {"null", "none", "nan", "#n/a", "na", "n/a", "-"}:
            return DataTypeEnum.NULL, None

        # Check boolean
        if RE_BOOLEAN.match(str_val):
            bool_parsed = str_val.lower() in {"true", "yes", "ya", "t", "y"}
            return DataTypeEnum.BOOLEAN, bool_parsed

        # Check percentage
        if RE_PERCENTAGE.match(str_val):
            try:
                num_part = str_val.replace("%", "").replace(",", "").strip()
                float_val = float(num_part) / 100.0
                return DataTypeEnum.PERCENTAGE, float_val
            except ValueError:
                pass

        # Check currency
        if RE_CURRENCY.match(str_val):
            try:
                cleaned = re.sub(r"[^\d.,\-+]", "", str_val).strip()
                # Normalize commas and dots: if both present or comma is thousands separator
                if "," in cleaned and "." in cleaned:
                    if cleaned.rfind(",") > cleaned.rfind("."):
                        cleaned = cleaned.replace(".", "").replace(",", ".")
                    else:
                        cleaned = cleaned.replace(",", "")
                elif "," in cleaned and "." not in cleaned:
                    # Could be decimal comma (e.g. European / Indonesian 10,50) or thousands (10,000)
                    if len(cleaned.split(",")[-1]) == 2:
                        cleaned = cleaned.replace(",", ".")
                    else:
                        cleaned = cleaned.replace(",", "")
                parsed_num = float(cleaned)
                return DataTypeEnum.CURRENCY, parsed_num
            except Exception:
                pass

        # Check clean integer
        # Handle formatted numbers like "1,000,000" or "1.000.000"
        int_clean = str_val.replace(",", "").replace(".", "")
        if RE_INTEGER.match(str_val):
            try:
                return DataTypeEnum.INTEGER, int(str_val)
            except ValueError:
                pass

        # Check float
        float_clean = str_val.replace(",", "")
        if RE_FLOAT.match(float_clean):
            try:
                return DataTypeEnum.FLOAT, float(float_clean)
            except ValueError:
                pass

        # Check standard date strings
        for fmt in DATE_FORMATS:
            try:
                parsed_dt = datetime.strptime(str_val, fmt)
                if "%H" in fmt:
                    return DataTypeEnum.DATETIME, parsed_dt.isoformat()
                return DataTypeEnum.DATE, parsed_dt.date().isoformat()
            except (ValueError, TypeError):
                continue

        # Default to String
        return DataTypeEnum.STRING, str_val

    @classmethod
    def profile_column_vector(
        cls,
        values: List[Any],
        column_name: str = "",
    ) -> Tuple[DataTypeEnum, SemanticTypeEnum, float, int, int, List[Any]]:
        """
        Profiles a list of values representing a column.
        Returns:
            (dominant_data_type, semantic_type, type_confidence, null_count, unique_count, sample_values)
        """
        total = len(values)
        if total == 0:
            return DataTypeEnum.UNKNOWN, SemanticTypeEnum.UNKNOWN, 0.0, 0, 0, []

        type_counts: dict[DataTypeEnum, int] = {}
        parsed_vals: List[Any] = []
        non_null_vals: List[Any] = []

        for v in values:
            dt, parsed = cls.detect_value_type(v)
            type_counts[dt] = type_counts.get(dt, 0) + 1
            parsed_vals.append(parsed)
            if dt != DataTypeEnum.NULL and parsed is not None:
                non_null_vals.append(parsed)

        null_count = type_counts.get(DataTypeEnum.NULL, 0)
        non_null_count = total - null_count
        unique_count = len(set(str(x) for x in non_null_vals))
        sample_values = non_null_vals[:5]

        if non_null_count == 0:
            return DataTypeEnum.NULL, SemanticTypeEnum.UNKNOWN, 1.0, null_count, 0, []

        # Find dominant physical type among non-null values
        best_type = DataTypeEnum.STRING
        best_count = 0
        for dt, count in type_counts.items():
            if dt == DataTypeEnum.NULL:
                continue
            if count > best_count:
                best_count = count
                best_type = dt

        confidence = round(best_count / non_null_count, 3)

        # Infer Semantic Type
        clean_name = column_name.lower().replace("_", " ").replace("-", " ").strip()
        name_tokens = set(clean_name.split())

        semantic = SemanticTypeEnum.UNKNOWN

        # 1. Identifier check
        if bool(name_tokens & IDENTIFIER_KEYWORDS) or (
            unique_count == non_null_count and non_null_count > 3 and best_type in {DataTypeEnum.STRING, DataTypeEnum.INTEGER}
        ):
            semantic = SemanticTypeEnum.IDENTIFIER
        # 2. Temporal check
        elif best_type in {DataTypeEnum.DATE, DataTypeEnum.DATETIME} or bool(name_tokens & TEMPORAL_KEYWORDS):
            semantic = SemanticTypeEnum.TEMPORAL
        # 3. Numeric measure check
        elif best_type in {DataTypeEnum.CURRENCY, DataTypeEnum.PERCENTAGE, DataTypeEnum.FLOAT} or (
            best_type == DataTypeEnum.INTEGER and (bool(name_tokens & MEASURE_KEYWORDS) or unique_count > 10)
        ):
            semantic = SemanticTypeEnum.NUMERIC_MEASURE
        # 4. Boolean
        elif best_type == DataTypeEnum.BOOLEAN:
            semantic = SemanticTypeEnum.BOOLEAN
        # 5. Categorical check
        elif best_type == DataTypeEnum.STRING:
            cardinality_ratio = unique_count / non_null_count if non_null_count > 0 else 1.0
            if cardinality_ratio <= 0.6 or bool(name_tokens & CATEGORICAL_KEYWORDS):
                semantic = SemanticTypeEnum.CATEGORICAL
            else:
                semantic = SemanticTypeEnum.TEXT
        else:
            semantic = SemanticTypeEnum.UNKNOWN

        return best_type, semantic, confidence, null_count, unique_count, sample_values
