"""
LABBAIK AI - Peak Season Calendar V1.2
======================================
Auto-boost refresh & risk based on peak seasons.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple
from enum import Enum


class SeasonType(str, Enum):
    """Season types affecting demand."""
    RAMADAN = "RAMADAN"
    HAJJ = "HAJJ"
    SCHOOL_HOLIDAY_ID = "SCHOOL_HOLIDAY_ID"  # Indonesia
    SCHOOL_HOLIDAY_MY = "SCHOOL_HOLIDAY_MY"  # Malaysia
    EID_FITR = "EID_FITR"
    EID_ADHA = "EID_ADHA"
    NEW_YEAR = "NEW_YEAR"
    MAULID = "MAULID"
    ISRA_MIRAJ = "ISRA_MIRAJ"
    LOW_SEASON = "LOW_SEASON"


@dataclass
class SeasonPeriod:
    """A peak/low season period."""
    name: str
    season_type: SeasonType
    start_date: date
    end_date: date
    weight: float  # 1.0 = normal, 1.5 = high, 2.0 = peak
    description: str = ""


# =============================================================================
# SEASON CALENDAR 2025-2026 (Approximate - Hijri dates vary)
# =============================================================================

SEASON_CALENDAR_2025: List[SeasonPeriod] = [
    # Ramadan 2025 (approx March 1 - March 30)
    SeasonPeriod(
        name="Ramadan 2025",
        season_type=SeasonType.RAMADAN,
        start_date=date(2025, 3, 1),
        end_date=date(2025, 3, 30),
        weight=1.8,
        description="Bulan puasa - demand sangat tinggi terutama 10 hari terakhir"
    ),
    # Eid Fitr 2025 (approx March 31 - April 5)
    SeasonPeriod(
        name="Idul Fitri 2025",
        season_type=SeasonType.EID_FITR,
        start_date=date(2025, 3, 31),
        end_date=date(2025, 4, 5),
        weight=2.0,
        description="Lebaran - peak demand, harga tertinggi"
    ),
    # Hajj 2025 (approx June 4-9)
    SeasonPeriod(
        name="Musim Haji 2025",
        season_type=SeasonType.HAJJ,
        start_date=date(2025, 5, 25),
        end_date=date(2025, 6, 15),
        weight=2.0,
        description="Musim haji - hotel Makkah sangat terbatas untuk umrah"
    ),
    # Eid Adha 2025 (approx June 7-12)
    SeasonPeriod(
        name="Idul Adha 2025",
        season_type=SeasonType.EID_ADHA,
        start_date=date(2025, 6, 7),
        end_date=date(2025, 6, 12),
        weight=2.0,
        description="Hari Raya Haji"
    ),
    # Indonesia School Holiday (June-July)
    SeasonPeriod(
        name="Libur Sekolah Indonesia",
        season_type=SeasonType.SCHOOL_HOLIDAY_ID,
        start_date=date(2025, 6, 15),
        end_date=date(2025, 7, 15),
        weight=1.5,
        description="Libur sekolah Indonesia - banyak keluarga umrah"
    ),
    # Indonesia School Holiday (Dec-Jan)
    SeasonPeriod(
        name="Libur Akhir Tahun",
        season_type=SeasonType.SCHOOL_HOLIDAY_ID,
        start_date=date(2025, 12, 20),
        end_date=date(2026, 1, 5),
        weight=1.6,
        description="Libur Natal & Tahun Baru"
    ),
    # New Year
    SeasonPeriod(
        name="Tahun Baru 2026",
        season_type=SeasonType.NEW_YEAR,
        start_date=date(2025, 12, 28),
        end_date=date(2026, 1, 3),
        weight=1.4,
        description="Libur tahun baru"
    ),
]

SEASON_CALENDAR_2026: List[SeasonPeriod] = [
    # Ramadan 2026 (approx Feb 18 - March 19)
    SeasonPeriod(
        name="Ramadan 2026",
        season_type=SeasonType.RAMADAN,
        start_date=date(2026, 2, 18),
        end_date=date(2026, 3, 19),
        weight=1.8,
        description="Bulan puasa"
    ),
    # Eid Fitr 2026 (approx March 20-25)
    SeasonPeriod(
        name="Idul Fitri 2026",
        season_type=SeasonType.EID_FITR,
        start_date=date(2026, 3, 20),
        end_date=date(2026, 3, 25),
        weight=2.0,
        description="Lebaran"
    ),
    # Hajj 2026 (approx May 25 - June 5)
    SeasonPeriod(
        name="Musim Haji 2026",
        season_type=SeasonType.HAJJ,
        start_date=date(2026, 5, 15),
        end_date=date(2026, 6, 5),
        weight=2.0,
        description="Musim haji"
    ),
]

# Combine all seasons
ALL_SEASONS = SEASON_CALENDAR_2025 + SEASON_CALENDAR_2026


class SeasonCalendar:
    """Peak season calendar service."""

    def __init__(self, seasons: List[SeasonPeriod] = None):
        self.seasons = seasons or ALL_SEASONS

    def get_season(self, check_date: date) -> Optional[SeasonPeriod]:
        """
        Get the season for a specific date.

        Args:
            check_date: Date to check

        Returns:
            SeasonPeriod if in peak season, None otherwise
        """
        for season in self.seasons:
            if season.start_date <= check_date <= season.end_date:
                return season
        return None

    def get_weight(self, check_date: date) -> float:
        """
        Get demand weight for a date.

        Args:
            check_date: Date to check

        Returns:
            Weight multiplier (1.0 = normal, up to 2.0 = peak)
        """
        season = self.get_season(check_date)
        return season.weight if season else 1.0

    def get_weight_range(self, start_date: date, end_date: date) -> float:
        """
        Get maximum weight across a date range.

        Args:
            start_date: Check-in date
            end_date: Check-out date

        Returns:
            Maximum weight in the range
        """
        max_weight = 1.0
        current = start_date

        while current <= end_date:
            w = self.get_weight(current)
            if w > max_weight:
                max_weight = w
            # Move to next day
            current = current + timedelta(days=1)

            # Safety limit
            if (current - start_date).days > 30:
                break

        return max_weight

    def is_peak_season(self, check_date: date) -> bool:
        """Check if date is in peak season (weight >= 1.5)."""
        return self.get_weight(check_date) >= 1.5

    def get_upcoming_peaks(
        self,
        from_date: date = None,
        limit: int = 5
    ) -> List[SeasonPeriod]:
        """
        Get upcoming peak seasons.

        Args:
            from_date: Start date (default: today)
            limit: Max results

        Returns:
            List of upcoming SeasonPeriod
        """
        if from_date is None:
            from_date = date.today()

        upcoming = [
            s for s in self.seasons
            if s.end_date >= from_date and s.weight >= 1.5
        ]

        # Sort by start date
        upcoming.sort(key=lambda x: x.start_date)

        return upcoming[:limit]

    def get_low_season_dates(
        self,
        year: int = 2025,
        min_gap_days: int = 14
    ) -> List[Tuple[date, date]]:
        """
        Find low season gaps (good for budget travel).

        Args:
            year: Year to check
            min_gap_days: Minimum consecutive low-season days

        Returns:
            List of (start, end) date tuples for low seasons
        """
        year_seasons = [
            s for s in self.seasons
            if s.start_date.year == year and s.weight >= 1.4
        ]

        if not year_seasons:
            return [(date(year, 1, 1), date(year, 12, 31))]

        # Sort by start
        year_seasons.sort(key=lambda x: x.start_date)

        gaps = []

        # Gap before first peak
        first_peak = year_seasons[0]
        if (first_peak.start_date - date(year, 1, 1)).days >= min_gap_days:
            gaps.append((date(year, 1, 1), first_peak.start_date))

        # Gaps between peaks
        for i in range(len(year_seasons) - 1):
            gap_start = year_seasons[i].end_date
            gap_end = year_seasons[i + 1].start_date
            if (gap_end - gap_start).days >= min_gap_days:
                gaps.append((gap_start, gap_end))

        # Gap after last peak
        last_peak = year_seasons[-1]
        if (date(year, 12, 31) - last_peak.end_date).days >= min_gap_days:
            gaps.append((last_peak.end_date, date(year, 12, 31)))

        return gaps

    def get_booking_recommendation(self, check_date: date) -> dict:
        """
        Get booking recommendation based on season.

        Args:
            check_date: Planned travel date

        Returns:
            Recommendation dict
        """
        season = self.get_season(check_date)
        weight = self.get_weight(check_date)

        if weight >= 1.8:
            urgency = "CRITICAL"
            advance_days = 90
            price_impact = "+50-100%"
            recommendation = "Book 3+ bulan sebelumnya. Harga & ketersediaan sangat terbatas."
        elif weight >= 1.5:
            urgency = "HIGH"
            advance_days = 60
            price_impact = "+30-50%"
            recommendation = "Book 2 bulan sebelumnya. Demand tinggi."
        elif weight >= 1.3:
            urgency = "MEDIUM"
            advance_days = 30
            price_impact = "+10-30%"
            recommendation = "Book 1 bulan sebelumnya untuk harga terbaik."
        else:
            urgency = "LOW"
            advance_days = 14
            price_impact = "Normal"
            recommendation = "Fleksibel. Banyak pilihan tersedia."

        return {
            "date": check_date.isoformat(),
            "season": season.name if season else "Regular",
            "season_type": season.season_type.value if season else None,
            "weight": weight,
            "urgency": urgency,
            "recommended_advance_booking_days": advance_days,
            "expected_price_impact": price_impact,
            "recommendation": recommendation,
        }


# Singleton instance
_calendar: Optional[SeasonCalendar] = None


def get_season_calendar() -> SeasonCalendar:
    """Get singleton SeasonCalendar instance."""
    global _calendar
    if _calendar is None:
        _calendar = SeasonCalendar()
    return _calendar


# Convenience functions
def season_weight(check_date: date) -> float:
    """Get season weight for a date."""
    return get_season_calendar().get_weight(check_date)


def is_peak_season(check_date: date) -> bool:
    """Check if date is peak season."""
    return get_season_calendar().is_peak_season(check_date)


def get_booking_recommendation(check_date: date) -> dict:
    """Get booking recommendation."""
    return get_season_calendar().get_booking_recommendation(check_date)
