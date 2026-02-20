"""
LABBAIK AI v6.0 - Notification Service
======================================
Handles email, WhatsApp, and in-app notifications.
"""

from __future__ import annotations
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
from enum import Enum
import json
import os

from core.config import get_settings
from core.exceptions import EmailServiceError, ExternalServiceError

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & DATA CLASSES
# =============================================================================

class NotificationChannel(str, Enum):
    """Notification channels."""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    IN_APP = "in_app"
    PUSH = "push"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationType(str, Enum):
    """Notification types."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    BOOKING = "booking"
    PAYMENT = "payment"
    REMINDER = "reminder"
    PROMOTION = "promotion"
    WELCOME = "welcome"
    VERIFICATION = "verification"


@dataclass
class NotificationMessage:
    """Notification message data."""
    recipient_id: str
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    
    channel: NotificationChannel = NotificationChannel.EMAIL
    type: NotificationType = NotificationType.INFO
    priority: NotificationPriority = NotificationPriority.NORMAL
    
    subject: str = ""
    title: str = ""
    body: str = ""
    html_body: Optional[str] = None
    
    data: Dict[str, Any] = field(default_factory=dict)
    template_id: Optional[str] = None
    
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class NotificationResult:
    """Notification send result."""
    success: bool
    message_id: Optional[str] = None
    channel: Optional[NotificationChannel] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# EMAIL TEMPLATES
# =============================================================================

class EmailTemplates:
    """Email template definitions."""
    
    BASE_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #1B4D3E 0%, #2E7D32 100%);
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 8px 8px 0 0;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
            }}
            .content {{
                background: #fff;
                padding: 30px;
                border: 1px solid #e0e0e0;
            }}
            .footer {{
                background: #f5f5f5;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #666;
                border-radius: 0 0 8px 8px;
            }}
            .button {{
                display: inline-block;
                background: #1B4D3E;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 4px;
                margin: 10px 0;
            }}
            .highlight {{
                background: #f0f7f4;
                padding: 15px;
                border-left: 4px solid #1B4D3E;
                margin: 15px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🕋 LABBAIK AI</h1>
        </div>
        <div class="content">
            {content}
        </div>
        <div class="footer">
            <p>© 2024 LABBAIK AI - Asisten Perjalanan Umrah Cerdas</p>
            <p>Powered by MS Hadianto</p>
        </div>
    </body>
    </html>
    """
    
    WELCOME = """
    <h2>Assalamu'alaikum, {name}! 🌙</h2>
    <p>Selamat datang di <strong>LABBAIK AI</strong> - platform cerdas untuk membantu 
    perjalanan ibadah Umrah Anda.</p>
    
    <div class="highlight">
        <strong>Fitur yang bisa Anda nikmati:</strong>
        <ul>
            <li>💬 Tanya jawab seputar Umrah dengan AI</li>
            <li>🧮 Simulasi biaya perjalanan</li>
            <li>📖 Panduan lengkap ibadah Umrah</li>
            <li>👥 Temukan partner perjalanan</li>
        </ul>
    </div>
    
    <p>
        <a href="{app_url}" class="button">Mulai Sekarang</a>
    </p>
    
    <p>Semoga Allah SWT memudahkan perjalanan ibadah Anda. Aamiin.</p>
    """
    
    VERIFICATION = """
    <h2>Verifikasi Email Anda</h2>
    <p>Halo {name},</p>
    <p>Terima kasih telah mendaftar di LABBAIK AI. Silakan klik tombol di bawah 
    untuk memverifikasi alamat email Anda:</p>
    
    <p style="text-align: center;">
        <a href="{verification_url}" class="button">Verifikasi Email</a>
    </p>
    
    <p><small>Link ini akan kedaluwarsa dalam 24 jam.</small></p>
    
    <p>Jika Anda tidak mendaftar di LABBAIK AI, abaikan email ini.</p>
    """
    
    BOOKING_CONFIRMATION = """
    <h2>Konfirmasi Booking Anda</h2>
    <p>Halo {name},</p>
    <p>Terima kasih telah melakukan booking di LABBAIK AI.</p>
    
    <div class="highlight">
        <strong>Detail Booking:</strong>
        <p>
            <strong>Nomor Booking:</strong> {booking_number}<br>
            <strong>Tanggal Berangkat:</strong> {departure_date}<br>
            <strong>Kota Keberangkatan:</strong> {departure_city}<br>
            <strong>Jumlah Jamaah:</strong> {traveler_count} orang<br>
            <strong>Total:</strong> Rp {total_price}
        </p>
    </div>
    
    <p>
        <a href="{booking_url}" class="button">Lihat Detail Booking</a>
    </p>
    
    <p>Tim kami akan segera menghubungi Anda untuk proses selanjutnya.</p>
    """
    
    PAYMENT_REMINDER = """
    <h2>Pengingat Pembayaran</h2>
    <p>Halo {name},</p>
    <p>Ini adalah pengingat untuk melakukan pembayaran booking Anda:</p>
    
    <div class="highlight">
        <strong>Nomor Booking:</strong> {booking_number}<br>
        <strong>Jumlah:</strong> Rp {amount}<br>
        <strong>Batas Waktu:</strong> {due_date}
    </div>
    
    <p>
        <a href="{payment_url}" class="button">Bayar Sekarang</a>
    </p>
    
    <p><small>Booking akan otomatis dibatalkan jika pembayaran tidak dilakukan 
    sebelum batas waktu.</small></p>
    """
    
    PASSWORD_RESET = """
    <h2>Reset Password</h2>
    <p>Halo {name},</p>
    <p>Kami menerima permintaan untuk reset password akun LABBAIK AI Anda.</p>

    <p style="text-align: center;">
        <a href="{reset_url}" class="button">Reset Password</a>
    </p>

    <p><small>Link ini akan kedaluwarsa dalam 1 jam.</small></p>

    <p>Jika Anda tidak meminta reset password, abaikan email ini.</p>
    """


# =============================================================================
# NOTIFICATION TEMPLATES (Multi-Channel)
# =============================================================================

NOTIFICATION_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "welcome": {
        "subject": "Selamat Datang di LABBAIK AI!",
        "body_template": (
            "Assalamu'alaikum {name}! Selamat datang di LABBAIK AI - "
            "platform cerdas untuk merencanakan perjalanan Umrah Anda. "
            "Mulai eksplorasi fitur simulasi biaya, perbandingan harga hotel, "
            "dan panduan ibadah lengkap. Semoga Allah SWT memudahkan perjalanan "
            "ibadah Anda. Aamiin."
        ),
        "channel": NotificationChannel.IN_APP,
        "priority": NotificationPriority.NORMAL,
        "type": NotificationType.WELCOME,
    },
    "booking_confirmation": {
        "subject": "Simulasi Booking Anda Tersimpan",
        "body_template": (
            "Halo {name}, simulasi booking Anda dengan nomor {booking_number} "
            "telah berhasil disimpan. Detail: berangkat dari {departure_city} "
            "pada {departure_date}, jumlah jamaah {traveler_count} orang, "
            "estimasi total Rp {total_price}. Silakan lanjutkan ke tahap "
            "pembayaran atau hubungi travel agent partner kami."
        ),
        "channel": NotificationChannel.EMAIL,
        "priority": NotificationPriority.HIGH,
        "type": NotificationType.BOOKING,
    },
    "payment_reminder": {
        "subject": "Pengingat Pembayaran Cicilan Umrah",
        "body_template": (
            "Halo {name}, ini adalah pengingat untuk pembayaran cicilan "
            "booking {booking_number}. Jumlah yang harus dibayar: "
            "Rp {amount}. Batas waktu pembayaran: {due_date}. "
            "Mohon segera lakukan pembayaran agar booking Anda tetap aktif."
        ),
        "channel": NotificationChannel.EMAIL,
        "priority": NotificationPriority.URGENT,
        "type": NotificationType.PAYMENT,
    },
    "doc_deadline": {
        "subject": "Batas Waktu Dokumen Mendekat",
        "body_template": (
            "Halo {name}, dokumen {document_type} Anda harus diserahkan "
            "paling lambat {deadline_date}. Sisa waktu: {days_remaining} hari. "
            "Pastikan dokumen sudah lengkap dan sesuai persyaratan. "
            "Buka halaman Cek Dokumen untuk panduan lengkap."
        ),
        "channel": NotificationChannel.IN_APP,
        "priority": NotificationPriority.HIGH,
        "type": NotificationType.REMINDER,
    },
    "departure_reminder": {
        "subject": "Persiapan Keberangkatan Umrah",
        "body_template": (
            "Halo {name}, keberangkatan Umrah Anda tinggal {days_remaining} "
            "hari lagi! Pastikan semua dokumen (paspor, visa, tiket) sudah "
            "lengkap. Cek kesiapan Anda di halaman Readiness Check. "
            "Jangan lupa ikuti manasik terakhir sebelum berangkat. "
            "Semoga perjalanan Anda lancar dan penuh berkah."
        ),
        "channel": NotificationChannel.WHATSAPP,
        "priority": NotificationPriority.HIGH,
        "type": NotificationType.REMINDER,
    },
    "group_invite": {
        "subject": "Undangan Bergabung Grup Umrah",
        "body_template": (
            "Assalamu'alaikum {name}, Anda diundang oleh {inviter_name} "
            "untuk bergabung ke grup Umrah \"{group_name}\". "
            "Bergabunglah untuk merencanakan perjalanan bersama, "
            "berbagi biaya, dan saling mendukung. "
            "Klik link berikut untuk bergabung: {join_link}"
        ),
        "channel": NotificationChannel.IN_APP,
        "priority": NotificationPriority.NORMAL,
        "type": NotificationType.INFO,
    },
    "referral_reward": {
        "subject": "Bonus Referral Anda Telah Diterima!",
        "body_template": (
            "Alhamdulillah {name}! Referral Anda berhasil. "
            "{referred_name} telah mendaftar menggunakan kode referral Anda. "
            "Anda mendapatkan bonus {reward_amount} poin yang bisa "
            "digunakan untuk diskon layanan premium. "
            "Total poin Anda saat ini: {total_points} poin."
        ),
        "channel": NotificationChannel.IN_APP,
        "priority": NotificationPriority.NORMAL,
        "type": NotificationType.SUCCESS,
    },
    "readiness_update": {
        "subject": "Skor Kesiapan Umrah Anda Meningkat",
        "body_template": (
            "Halo {name}, skor kesiapan Umrah Anda meningkat menjadi "
            "{readiness_score}%! {completion_message} "
            "Lanjutkan persiapan Anda untuk mencapai skor 100%. "
            "Buka halaman Readiness Check untuk melihat detail lengkap."
        ),
        "channel": NotificationChannel.IN_APP,
        "priority": NotificationPriority.LOW,
        "type": NotificationType.SUCCESS,
    },
    "price_alert": {
        "subject": "Harga Paket Umrah Turun!",
        "body_template": (
            "Kabar baik {name}! Harga paket \"{package_name}\" turun dari "
            "Rp {old_price} menjadi Rp {new_price} (hemat {discount_percent}%). "
            "Promo ini berlaku hingga {valid_until}. "
            "Segera cek dan booking sebelum harga naik kembali."
        ),
        "channel": NotificationChannel.WHATSAPP,
        "priority": NotificationPriority.HIGH,
        "type": NotificationType.PROMOTION,
    },
    "manasik_reminder": {
        "subject": "Pengingat Jadwal Manasik Umrah",
        "body_template": (
            "Halo {name}, jadwal manasik Umrah Anda akan dimulai pada "
            "{manasik_date} pukul {manasik_time} di {manasik_location}. "
            "Materi yang akan dibahas: {manasik_topic}. "
            "Harap hadir tepat waktu dan bawa catatan. "
            "Semoga manasik kali ini bermanfaat untuk persiapan ibadah Anda."
        ),
        "channel": NotificationChannel.WHATSAPP,
        "priority": NotificationPriority.NORMAL,
        "type": NotificationType.REMINDER,
    },
}


# =============================================================================
# WHATSAPP TEMPLATES
# =============================================================================

class WhatsAppTemplates:
    """Template pesan WhatsApp untuk berbagai notifikasi Umrah."""

    @staticmethod
    def booking_summary(booking_data: Dict[str, Any]) -> str:
        """
        Format ringkasan booking untuk WhatsApp.

        Args:
            booking_data: Dict berisi booking_number, name, departure_city,
                          departure_date, traveler_count, total_price, hotel_name,
                          flight_info (semua opsional kecuali booking_number).

        Returns:
            Pesan WhatsApp terformat.
        """
        booking_number = booking_data.get("booking_number", "-")
        name = booking_data.get("name", "Jamaah")
        departure_city = booking_data.get("departure_city", "-")
        departure_date = booking_data.get("departure_date", "-")
        traveler_count = booking_data.get("traveler_count", 1)
        total_price = booking_data.get("total_price", "-")
        hotel_name = booking_data.get("hotel_name", "-")
        flight_info = booking_data.get("flight_info", "-")

        return (
            f"Assalamu'alaikum {name},\n\n"
            f"Berikut ringkasan booking Umrah Anda:\n\n"
            f"No. Booking: {booking_number}\n"
            f"Kota Keberangkatan: {departure_city}\n"
            f"Tanggal Berangkat: {departure_date}\n"
            f"Jumlah Jamaah: {traveler_count} orang\n"
            f"Hotel: {hotel_name}\n"
            f"Penerbangan: {flight_info}\n"
            f"Total Biaya: Rp {total_price}\n\n"
            f"Untuk detail selengkapnya, silakan buka aplikasi LABBAIK AI.\n\n"
            f"Jazakallahu khairan."
        )

    @staticmethod
    def price_alert(package_name: str, old_price: str, new_price: str) -> str:
        """
        Format notifikasi penurunan harga untuk WhatsApp.

        Args:
            package_name: Nama paket Umrah.
            old_price: Harga lama (sudah diformat, misal "25.000.000").
            new_price: Harga baru (sudah diformat, misal "22.000.000").

        Returns:
            Pesan WhatsApp terformat.
        """
        return (
            f"Kabar baik! Harga paket Umrah turun.\n\n"
            f"Paket: {package_name}\n"
            f"Harga Lama: Rp {old_price}\n"
            f"Harga Baru: Rp {new_price}\n\n"
            f"Segera cek dan booking sebelum harga naik kembali.\n"
            f"Buka aplikasi LABBAIK AI untuk detail lengkap.\n\n"
            f"Jazakallahu khairan."
        )

    @staticmethod
    def group_invite(group_name: str, inviter_name: str, join_link: str) -> str:
        """
        Format undangan grup Umrah untuk WhatsApp.

        Args:
            group_name: Nama grup Umrah.
            inviter_name: Nama orang yang mengundang.
            join_link: Link untuk bergabung ke grup.

        Returns:
            Pesan WhatsApp terformat.
        """
        return (
            f"Assalamu'alaikum,\n\n"
            f"{inviter_name} mengundang Anda untuk bergabung ke grup Umrah "
            f"\"{group_name}\" di LABBAIK AI.\n\n"
            f"Bergabunglah untuk:\n"
            f"- Merencanakan perjalanan bersama\n"
            f"- Berbagi estimasi biaya\n"
            f"- Koordinasi jadwal keberangkatan\n"
            f"- Saling mendukung persiapan ibadah\n\n"
            f"Klik link berikut untuk bergabung:\n"
            f"{join_link}\n\n"
            f"Jazakallahu khairan."
        )

    @staticmethod
    def departure_countdown(
        name: str, days: int, checklist_items: List[str]
    ) -> str:
        """
        Format pesan hitung mundur keberangkatan untuk WhatsApp.

        Args:
            name: Nama jamaah.
            days: Jumlah hari sebelum keberangkatan.
            checklist_items: Daftar item checklist yang perlu disiapkan.

        Returns:
            Pesan WhatsApp terformat.
        """
        checklist_text = ""
        for item in checklist_items:
            checklist_text += f"- {item}\n"

        if not checklist_items:
            checklist_text = "- Semua persiapan sudah lengkap!\n"

        return (
            f"Assalamu'alaikum {name},\n\n"
            f"Keberangkatan Umrah Anda tinggal *{days} hari* lagi!\n\n"
            f"Checklist persiapan:\n"
            f"{checklist_text}\n"
            f"Pastikan semua dokumen dan perlengkapan sudah siap.\n"
            f"Buka aplikasi LABBAIK AI untuk cek kesiapan lengkap.\n\n"
            f"Semoga Allah SWT memudahkan dan memberkahi perjalanan ibadah Anda.\n"
            f"Aamiin ya Rabbal Alamin."
        )


# =============================================================================
# IN-APP TEMPLATES
# =============================================================================

class InAppTemplates:
    """Template notifikasi in-app dengan format HTML."""

    # Mapping tipe notifikasi ke ikon dan warna
    _TYPE_STYLES: Dict[str, Dict[str, str]] = {
        "info": {"icon": "info", "color": "#2196F3", "bg": "#E3F2FD"},
        "success": {"icon": "check_circle", "color": "#4CAF50", "bg": "#E8F5E9"},
        "warning": {"icon": "warning", "color": "#FF9800", "bg": "#FFF3E0"},
        "error": {"icon": "error", "color": "#F44336", "bg": "#FFEBEE"},
        "booking": {"icon": "flight_takeoff", "color": "#1B4D3E", "bg": "#E8F5E9"},
        "payment": {"icon": "payments", "color": "#FF9800", "bg": "#FFF3E0"},
        "reminder": {"icon": "notifications_active", "color": "#9C27B0", "bg": "#F3E5F5"},
        "promotion": {"icon": "local_offer", "color": "#E91E63", "bg": "#FCE4EC"},
        "welcome": {"icon": "celebration", "color": "#1B4D3E", "bg": "#E8F5E9"},
        "verification": {"icon": "verified", "color": "#2196F3", "bg": "#E3F2FD"},
    }

    @staticmethod
    def render_notification_html(template_id: str, context: Dict[str, Any]) -> str:
        """
        Render notifikasi HTML dari template yang terdaftar.

        Args:
            template_id: ID template dari NOTIFICATION_TEMPLATES.
            context: Dict variabel untuk substitusi placeholder.

        Returns:
            String HTML untuk ditampilkan di dalam aplikasi.
        """
        template = NOTIFICATION_TEMPLATES.get(template_id)
        if not template:
            return (
                '<div style="padding:12px;color:#F44336;">'
                f"Template tidak ditemukan: {template_id}</div>"
            )

        # Substitusi placeholder di body
        try:
            body = template["body_template"].format(**context)
        except KeyError as e:
            body = (
                f"Gagal memformat template: variabel {e} tidak tersedia."
            )

        subject = template["subject"]
        notif_type = template["type"].value if isinstance(
            template["type"], NotificationType
        ) else str(template["type"])

        style = InAppTemplates._TYPE_STYLES.get(
            notif_type, InAppTemplates._TYPE_STYLES["info"]
        )

        return (
            f'<div style="border-left:4px solid {style["color"]};'
            f'background:{style["bg"]};padding:16px;border-radius:8px;'
            f'margin-bottom:12px;font-family:sans-serif;" '
            f'role="status" aria-live="polite">'
            f'<div style="display:flex;align-items:center;margin-bottom:8px;">'
            f'<span style="font-size:20px;margin-right:8px;color:{style["color"]};"'
            f' aria-hidden="true">'
            f'<span class="material-icons">{style["icon"]}</span></span>'
            f'<strong style="font-size:15px;color:#333;">{subject}</strong>'
            f"</div>"
            f'<p style="margin:0;color:#555;font-size:14px;line-height:1.6;">'
            f"{body}</p>"
            f"</div>"
        )

    @staticmethod
    def render_notification_toast(
        title: str, message: str, type: str = "info"
    ) -> str:
        """
        Render notifikasi gaya toast untuk tampilan singkat.

        Args:
            title: Judul notifikasi.
            message: Pesan notifikasi.
            type: Tipe notifikasi (info/success/warning/error).

        Returns:
            String HTML bergaya toast.
        """
        style = InAppTemplates._TYPE_STYLES.get(
            type, InAppTemplates._TYPE_STYLES["info"]
        )

        return (
            f'<div style="position:fixed;top:20px;right:20px;z-index:9999;'
            f"min-width:320px;max-width:420px;padding:16px 20px;"
            f"border-radius:10px;box-shadow:0 4px 20px rgba(0,0,0,0.15);"
            f'background:{style["bg"]};border-left:4px solid {style["color"]};" '
            f'role="alert" aria-live="assertive">'
            f'<div style="display:flex;align-items:center;margin-bottom:6px;">'
            f'<span style="font-size:18px;margin-right:8px;color:{style["color"]};"'
            f' aria-hidden="true">'
            f'<span class="material-icons">{style["icon"]}</span></span>'
            f'<strong style="font-size:14px;color:#333;">{title}</strong>'
            f"</div>"
            f'<p style="margin:0;color:#555;font-size:13px;line-height:1.5;">'
            f"{message}</p>"
            f"</div>"
        )


# =============================================================================
# TEMPLATE RENDERING FUNCTIONS
# =============================================================================

def render_template(
    template_id: str, context: Dict[str, Any]
) -> Optional[NotificationMessage]:
    """
    Render template notifikasi menjadi NotificationMessage siap kirim.

    Mencari template berdasarkan template_id di NOTIFICATION_TEMPLATES,
    lalu melakukan substitusi placeholder dengan nilai dari context dict.

    Args:
        template_id: ID template (misal 'welcome', 'price_alert').
        context: Dict berisi nilai untuk placeholder. Harus menyertakan
                 'recipient_id' dan opsional 'recipient_email', 'recipient_phone'.

    Returns:
        NotificationMessage yang siap dikirim, atau None jika template
        tidak ditemukan.
    """
    template = NOTIFICATION_TEMPLATES.get(template_id)
    if not template:
        logger.warning(f"Template notifikasi tidak ditemukan: {template_id}")
        return None

    # Substitusi placeholder di body_template
    try:
        body = template["body_template"].format(**context)
    except KeyError as e:
        logger.error(
            f"Gagal render template '{template_id}': variabel {e} tidak tersedia"
        )
        return None

    subject = template["subject"]

    return NotificationMessage(
        recipient_id=context.get("recipient_id", ""),
        recipient_email=context.get("recipient_email"),
        recipient_phone=context.get("recipient_phone"),
        channel=template["channel"],
        type=template["type"],
        priority=template["priority"],
        subject=subject,
        title=subject,
        body=body,
        template_id=template_id,
        data=context,
    )


def get_template_list() -> List[Dict[str, str]]:
    """
    Mengembalikan daftar template yang tersedia beserta deskripsinya.

    Returns:
        List of dicts dengan keys: 'id', 'subject', 'channel', 'priority', 'type'.
    """
    _DESCRIPTIONS: Dict[str, str] = {
        "welcome": "Pesan selamat datang untuk pengguna baru",
        "booking_confirmation": "Konfirmasi simulasi booking tersimpan",
        "payment_reminder": "Pengingat cicilan pembayaran Umrah",
        "doc_deadline": "Peringatan batas waktu penyerahan dokumen",
        "departure_reminder": "Hitung mundur hari keberangkatan",
        "group_invite": "Undangan bergabung ke grup Umrah",
        "referral_reward": "Notifikasi bonus referral diterima",
        "readiness_update": "Pembaruan skor kesiapan Umrah",
        "price_alert": "Notifikasi penurunan harga paket",
        "manasik_reminder": "Pengingat jadwal pelatihan manasik",
    }

    result = []
    for tid, tpl in NOTIFICATION_TEMPLATES.items():
        channel = tpl["channel"]
        priority = tpl["priority"]
        ntype = tpl["type"]
        result.append({
            "id": tid,
            "subject": tpl["subject"],
            "description": _DESCRIPTIONS.get(tid, tpl["subject"]),
            "channel": channel.value if isinstance(channel, NotificationChannel) else str(channel),
            "priority": priority.value if isinstance(priority, NotificationPriority) else str(priority),
            "type": ntype.value if isinstance(ntype, NotificationType) else str(ntype),
        })
    return result


# =============================================================================
# BASE NOTIFICATION SENDER
# =============================================================================

class BaseNotificationSender(ABC):
    """Abstract base for notification senders."""
    
    @property
    @abstractmethod
    def channel(self) -> NotificationChannel:
        """Return channel type."""
        pass
    
    @abstractmethod
    def send(self, message: NotificationMessage) -> NotificationResult:
        """Send notification."""
        pass
    
    @abstractmethod
    def send_batch(self, messages: List[NotificationMessage]) -> List[NotificationResult]:
        """Send batch notifications."""
        pass


# =============================================================================
# EMAIL SENDER
# =============================================================================

class EmailSender(BaseNotificationSender):
    """Email notification sender using SMTP."""
    
    def __init__(
        self,
        smtp_host: str = None,
        smtp_port: int = None,
        smtp_user: str = None,
        smtp_password: str = None,
        from_address: str = None,
        use_tls: bool = True
    ):
        settings = get_settings()
        
        self.smtp_host = smtp_host or os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.environ.get("SMTP_USER", "")
        self.smtp_password = smtp_password or os.environ.get("SMTP_PASSWORD", "")
        self.from_address = from_address or os.environ.get("EMAIL_FROM", "noreply@labbaik.io")
        self.use_tls = use_tls
        
        self._templates = EmailTemplates()
    
    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.EMAIL
    
    def send(self, message: NotificationMessage) -> NotificationResult:
        """
        Send email notification.
        
        Args:
            message: Notification message
        
        Returns:
            NotificationResult
        """
        if not message.recipient_email:
            return NotificationResult(
                success=False,
                channel=self.channel,
                error="Recipient email is required"
            )
        
        try:
            # Create email
            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.subject or message.title
            msg["From"] = self.from_address
            msg["To"] = message.recipient_email
            
            # Add plain text
            msg.attach(MIMEText(message.body, "plain"))
            
            # Add HTML if available
            if message.html_body:
                html_content = self._templates.BASE_TEMPLATE.format(
                    content=message.html_body
                )
                msg.attach(MIMEText(html_content, "html"))
            
            # Send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                
                server.sendmail(
                    self.from_address,
                    message.recipient_email,
                    msg.as_string()
                )
            
            logger.info(f"Email sent to {message.recipient_email}")
            
            return NotificationResult(
                success=True,
                channel=self.channel,
                message_id=f"email_{datetime.utcnow().timestamp()}"
            )
            
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return NotificationResult(
                success=False,
                channel=self.channel,
                error=f"SMTP error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return NotificationResult(
                success=False,
                channel=self.channel,
                error=str(e)
            )
    
    def send_batch(self, messages: List[NotificationMessage]) -> List[NotificationResult]:
        """Send batch emails."""
        results = []
        for msg in messages:
            results.append(self.send(msg))
        return results
    
    def send_template(
        self,
        template_name: str,
        recipient_email: str,
        recipient_name: str,
        subject: str,
        **template_vars
    ) -> NotificationResult:
        """
        Send email using template.
        
        Args:
            template_name: Template name (welcome, verification, etc.)
            recipient_email: Recipient email
            recipient_name: Recipient name
            subject: Email subject
            **template_vars: Template variables
        
        Returns:
            NotificationResult
        """
        template_map = {
            "welcome": self._templates.WELCOME,
            "verification": self._templates.VERIFICATION,
            "booking_confirmation": self._templates.BOOKING_CONFIRMATION,
            "payment_reminder": self._templates.PAYMENT_REMINDER,
            "password_reset": self._templates.PASSWORD_RESET,
        }
        
        template = template_map.get(template_name)
        if not template:
            return NotificationResult(
                success=False,
                error=f"Unknown template: {template_name}"
            )
        
        # Render template
        template_vars["name"] = recipient_name
        html_body = template.format(**template_vars)
        
        # Create message
        message = NotificationMessage(
            recipient_id="",
            recipient_email=recipient_email,
            subject=subject,
            title=subject,
            body=f"Email for {recipient_name}",
            html_body=html_body,
            type=NotificationType.INFO,
        )
        
        return self.send(message)


# =============================================================================
# IN-APP NOTIFICATION SENDER
# =============================================================================

class InAppNotificationSender(BaseNotificationSender):
    """In-app notification sender."""
    
    def __init__(self, notification_repository=None):
        self.repo = notification_repository
    
    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.IN_APP
    
    def send(self, message: NotificationMessage) -> NotificationResult:
        """
        Save notification to database for in-app display.
        
        Args:
            message: Notification message
        
        Returns:
            NotificationResult
        """
        try:
            notification_data = {
                "user_id": message.recipient_id,
                "type": message.type.value,
                "title": message.title,
                "message": message.body,
                "link": message.data.get("link"),
                "is_read": False,
                "created_at": datetime.utcnow(),
            }
            
            if self.repo:
                result = self.repo.create(notification_data)
                notification_id = result.id
            else:
                # In-memory for demo
                notification_id = f"notif_{datetime.utcnow().timestamp()}"
            
            logger.info(f"In-app notification created for user {message.recipient_id}")
            
            return NotificationResult(
                success=True,
                channel=self.channel,
                message_id=notification_id
            )
            
        except Exception as e:
            logger.error(f"In-app notification error: {e}")
            return NotificationResult(
                success=False,
                channel=self.channel,
                error=str(e)
            )
    
    def send_batch(self, messages: List[NotificationMessage]) -> List[NotificationResult]:
        """Send batch in-app notifications."""
        results = []
        for msg in messages:
            results.append(self.send(msg))
        return results


# =============================================================================
# NOTIFICATION SERVICE
# =============================================================================

class NotificationService:
    """
    Main notification service.
    Handles routing to appropriate channels.
    """
    
    _instance: Optional["NotificationService"] = None
    
    def __new__(cls) -> "NotificationService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._senders: Dict[NotificationChannel, BaseNotificationSender] = {}
        self._initialized = True
        
        # Register default senders
        self.register_sender(EmailSender())
        self.register_sender(InAppNotificationSender())
    
    def register_sender(self, sender: BaseNotificationSender):
        """Register a notification sender."""
        self._senders[sender.channel] = sender
        logger.info(f"Registered notification sender: {sender.channel.value}")
    
    def send(
        self,
        message: NotificationMessage,
        channels: List[NotificationChannel] = None
    ) -> Dict[NotificationChannel, NotificationResult]:
        """
        Send notification through specified channels.
        
        Args:
            message: Notification message
            channels: Channels to send through (defaults to message.channel)
        
        Returns:
            Dict of results per channel
        """
        channels = channels or [message.channel]
        results = {}
        
        for channel in channels:
            sender = self._senders.get(channel)
            if sender:
                results[channel] = sender.send(message)
            else:
                results[channel] = NotificationResult(
                    success=False,
                    channel=channel,
                    error=f"No sender registered for {channel.value}"
                )
        
        return results
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: str = None,
        **kwargs
    ) -> NotificationResult:
        """
        Convenience method for sending email.
        
        Args:
            to: Recipient email
            subject: Email subject
            body: Plain text body
            html: HTML body (optional)
        
        Returns:
            NotificationResult
        """
        message = NotificationMessage(
            recipient_id="",
            recipient_email=to,
            channel=NotificationChannel.EMAIL,
            subject=subject,
            title=subject,
            body=body,
            html_body=html,
            **kwargs
        )
        
        results = self.send(message)
        return results.get(NotificationChannel.EMAIL)
    
    def send_welcome_email(self, email: str, name: str, app_url: str = "https://labbaik.io") -> NotificationResult:
        """Send welcome email to new user."""
        sender = self._senders.get(NotificationChannel.EMAIL)
        if isinstance(sender, EmailSender):
            return sender.send_template(
                "welcome",
                recipient_email=email,
                recipient_name=name,
                subject="Selamat Datang di LABBAIK AI! 🕋",
                app_url=app_url
            )
        return NotificationResult(success=False, error="Email sender not available")
    
    def send_verification_email(self, email: str, name: str, verification_url: str) -> NotificationResult:
        """Send email verification."""
        sender = self._senders.get(NotificationChannel.EMAIL)
        if isinstance(sender, EmailSender):
            return sender.send_template(
                "verification",
                recipient_email=email,
                recipient_name=name,
                subject="Verifikasi Email LABBAIK AI",
                verification_url=verification_url
            )
        return NotificationResult(success=False, error="Email sender not available")
    
    def send_booking_confirmation(
        self,
        email: str,
        name: str,
        booking_number: str,
        departure_date: str,
        departure_city: str,
        traveler_count: int,
        total_price: str,
        booking_url: str
    ) -> NotificationResult:
        """Send booking confirmation email."""
        sender = self._senders.get(NotificationChannel.EMAIL)
        if isinstance(sender, EmailSender):
            return sender.send_template(
                "booking_confirmation",
                recipient_email=email,
                recipient_name=name,
                subject=f"Konfirmasi Booking {booking_number} - LABBAIK AI",
                booking_number=booking_number,
                departure_date=departure_date,
                departure_city=departure_city,
                traveler_count=traveler_count,
                total_price=total_price,
                booking_url=booking_url
            )
        return NotificationResult(success=False, error="Email sender not available")
    
    def notify_user(
        self,
        user_id: str,
        title: str,
        message: str,
        type: NotificationType = NotificationType.INFO,
        link: str = None
    ) -> NotificationResult:
        """
        Send in-app notification to user.
        
        Args:
            user_id: Target user ID
            title: Notification title
            message: Notification body
            type: Notification type
            link: Optional action link
        
        Returns:
            NotificationResult
        """
        msg = NotificationMessage(
            recipient_id=user_id,
            channel=NotificationChannel.IN_APP,
            type=type,
            title=title,
            body=message,
            data={"link": link} if link else {}
        )
        
        results = self.send(msg)
        return results.get(NotificationChannel.IN_APP)


def get_notification_service() -> NotificationService:
    """Get notification service singleton."""
    return NotificationService()
