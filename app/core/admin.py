from sqladmin import Admin, ModelView
from sqladmin.filters import BooleanFilter, AllUniqueStringValuesFilter, StaticValuesFilter
from sqlalchemy import func, select
from app.models.user import User
from app.models.patient import Patient
from app.models.fundus_image import FundusImage
from app.models.detection import Detection
from app.models.token_blacklist import TokenBlacklist
from app.core.config import settings
import os

# 1. Dapatkan path dari file ini (admin.py)
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 2. Keluar satu level (ke folder 'core'), lalu keluar lagi (ke folder 'app')
_APP_DIR = os.path.dirname(_BASE_DIR)
# 3. Gabungkan dengan folder 'templates/admin'
TEMPLATES_DIR = os.path.join(_APP_DIR, "templates/admin")

# -----------------------------
# User Admin Configuration
# -----------------------------
class UserAdmin(ModelView, model=User):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"

    # List view - tampil di table
    column_list = [
        User.id,
        User.full_name,
        User.email,
        User.phone_number,
        User.profession,
        User.province_name,
        User.city_name,
        User.is_active,
        User.created_at
    ]

    # Search functionality
    column_searchable_list = [
        User.full_name, 
        User.email, 
        User.profession,
        User.phone_number
    ]
    
    # Sortable columns
    column_sortable_list = [
        User.id, 
        User.full_name, 
        User.email, 
        User.created_at
    ]

    # Filters
    column_filters = [
        BooleanFilter(User.is_active),
        AllUniqueStringValuesFilter(User.profession),
        AllUniqueStringValuesFilter(User.province_name),
    ]

    # Default sorting
    column_default_sort = [(User.created_at, True)]

    # Detail view - tampil di detail page
    column_details_list = [
        User.id,
        User.full_name,
        User.email,
        User.phone_number,
        User.profession,
        User.date_of_birth,
        User.photo_url,
        User.province_name,
        User.city_name,
        User.district_name,
        User.village_name,
        User.detailed_address,
        User.assignment_location,
        User.is_active,
        User.otp,
        User.otp_expires_at,
        User.created_at,
        User.updated_at
    ]

    # Exclude sensitive fields from forms
    form_excluded_columns = [
        User.password_hash,
        User.refresh_token,
        User.otp,
        User.otp_expires_at,
        User.created_at, 
        User.updated_at
    ]

    # Column labels (human-readable)
    column_labels = {
        User.id: "ID",
        User.full_name: "Full Name",
        User.email: "Email",
        User.phone_number: "Phone",
        User.profession: "Profession",
        User.date_of_birth: "Date of Birth",
        User.photo_url: "Photo URL",
        User.province_name: "Province",
        User.city_name: "City",
        User.district_name: "District",
        User.village_name: "Village",
        User.detailed_address: "Detailed Address",
        User.assignment_location: "Assignment Location",
        User.is_active: "Active",
        User.otp: "OTP Code",
        User.otp_expires_at: "OTP Expires At",
        User.created_at: "Created At",
        User.updated_at: "Updated At"
    }

    # Column formatters (custom display)
    column_formatters = {
        User.phone_number: lambda m, a: m.phone_number or "-",
        User.photo_url: lambda m, a: "✅ Has Photo" if m.photo_url else "❌ No Photo"
    }


# -----------------------------
# Patient Admin Configuration
# -----------------------------
class PatientAdmin(ModelView, model=Patient):
    name = "Patient"
    name_plural = "Patients"
    icon = "fa-solid fa-hospital-user"

    # List view
    column_list = [
        Patient.id,
        Patient.patient_code,
        Patient.name,
        Patient.gender,
        Patient.date_of_birth,
        "creator.full_name",  # Show user name instead of ID
        Patient.created_at
    ]

    # Search
    column_searchable_list = [
        Patient.patient_code, 
        Patient.name
    ]
    
    # Sort
    column_sortable_list = [
        Patient.id, 
        Patient.patient_code, 
        Patient.name, 
        Patient.created_at
    ]

    # Filters
    column_filters = [
        AllUniqueStringValuesFilter(Patient.gender),
    ]

    # Default sort
    column_default_sort = [(Patient.created_at, True)]

    # Detail view - TAMPILKAN SEMUA!
    column_details_list = [
        Patient.id,
        Patient.patient_code,
        Patient.name,
        Patient.gender,
        Patient.date_of_birth,
        "creator",  # Show related user
        Patient.created_by_user_id,
        Patient.created_at,
        Patient.updated_at
    ]

    # Exclude from form
    form_excluded_columns = [
        Patient.created_at, 
        Patient.updated_at
    ]

    # Labels
    column_labels = {
        Patient.id: "ID",
        Patient.patient_code: "Patient Code",
        Patient.name: "Name",
        Patient.gender: "Gender",
        Patient.date_of_birth: "Date of Birth",
        Patient.created_by_user_id: "Created By User ID",
        "creator.full_name": "Created By",
        Patient.created_at: "Created At",
        Patient.updated_at: "Updated At"
    }


# -----------------------------
# Fundus Image Admin Configuration
# -----------------------------
class FundusImageAdmin(ModelView, model=FundusImage):
    name = "Fundus Image"
    name_plural = "Fundus Images"
    icon = "fa-solid fa-image"

    # List view
    column_list = [
        FundusImage.id,
        "patient.name",
        "user.full_name",
        FundusImage.side_eye,
        FundusImage.gcs_filename,
        FundusImage.uploaded_at
    ]

    # Search
    column_searchable_list = [
        FundusImage.gcs_filename
    ]
    
    # Sort
    column_sortable_list = [
        FundusImage.id, 
        FundusImage.uploaded_at
    ]

    # Filters
    column_filters = [
        AllUniqueStringValuesFilter(FundusImage.side_eye),
    ]

    # Default sort
    column_default_sort = [(FundusImage.uploaded_at, True)]

    # Detail view - TAMPILKAN SEMUA!
    column_details_list = [
        FundusImage.id,
        "patient", 
        "user", 
        FundusImage.patient_id,
        FundusImage.user_id,
        FundusImage.side_eye,
        FundusImage.image_url,
        FundusImage.gcs_filename,
        FundusImage.uploaded_at
    ]

    # Exclude from form
    form_excluded_columns = [
        FundusImage.uploaded_at
    ]

    # Labels
    column_labels = {
        FundusImage.id: "ID",
        FundusImage.patient_id: "Patient ID",
        FundusImage.user_id: "User ID",
        "patient.name": "Patient Name",
        "user.full_name": "Uploaded By",
        FundusImage.side_eye: "Eye Side",
        FundusImage.image_url: "Image URL",
        FundusImage.gcs_filename: "GCS Filename",
        FundusImage.uploaded_at: "Uploaded At"
    }

    # Formatters
    column_formatters = {
        FundusImage.image_url: lambda m, a: f"🖼️ {m.gcs_filename[:30]}..."
    }


# -----------------------------
# Detection Admin Configuration
# -----------------------------
class DetectionAdmin(ModelView, model=Detection):
    name = "Detection"
    name_plural = "Detections"
    icon = "fa-solid fa-eye"

    # List view
    column_list = [
        Detection.id,
        "patient.name",
        "user.full_name",
        Detection.classification,
        Detection.confidence,
        Detection.age_at_detection,
        Detection.detected_at
    ]

    # Search
    column_searchable_list = [
        Detection.description
    ]
    
    # Sort
    column_sortable_list = [
        Detection.id, 
        Detection.confidence, 
        Detection.detected_at, 
        Detection.created_at
    ]

    # Filters
    column_filters = [
        StaticValuesFilter(
            Detection.classification,
            values=[
                ("0", "No DR"),
                ("1", "Mild NPDR"),
                ("2", "Moderate NPDR"),
                ("3", "Severe NPDR"),
                ("4", "Proliferative DR")
            ]
        ),
    ]

    # Default sort
    column_default_sort = [(Detection.detected_at, True)]

    # Detail view - TAMPILKAN SEMUA!
    column_details_list = [
        Detection.id,
        "patient",
        "fundus_image",
        "user",
        Detection.patient_id,
        Detection.fundus_image_id,
        Detection.user_id,
        Detection.classification,
        Detection.confidence,
        Detection.age_at_detection,
        Detection.description,
        Detection.detected_at,
        Detection.created_at
    ]

    # Exclude from form
    form_excluded_columns = [
        Detection.created_at
    ]

    # Labels
    column_labels = {
        Detection.id: "ID",
        Detection.patient_id: "Patient ID",
        Detection.fundus_image_id: "Fundus Image ID",
        Detection.user_id: "User ID",
        "patient.name": "Patient Name",
        "user.full_name": "Detected By",
        Detection.classification: "Classification",
        Detection.confidence: "Confidence",
        Detection.age_at_detection: "Age at Detection",
        Detection.description: "Description",
        Detection.detected_at: "Detected At",
        Detection.created_at: "Created At"
    }

    # Formatters
    column_formatters = {
        Detection.confidence: lambda m, a: f"{m.confidence * 100:.2f}%",
        Detection.classification: lambda m, a: {
            0: "🟢 No DR",
            1: "🟡 Mild NPDR",
            2: "🟠 Moderate NPDR",
            3: "🔴 Severe NPDR",
            4: "⚫ Proliferative DR"
        }.get(m.classification, "Unknown")
    }


# -----------------------------
# Token Blacklist Admin Configuration
# -----------------------------
class TokenBlacklistAdmin(ModelView, model=TokenBlacklist):
    name = "Token Blacklist"
    name_plural = "Token Blacklist"
    icon = "fa-solid fa-ban"

    # List view
    column_list = [
        TokenBlacklist.id,
        TokenBlacklist.user_id,
        TokenBlacklist.blacklisted_at,
        TokenBlacklist.expires_at
    ]

    # Search
    column_searchable_list = [
        TokenBlacklist.token
    ]
    
    # Sort
    column_sortable_list = [
        TokenBlacklist.id,
        TokenBlacklist.user_id,
        TokenBlacklist.blacklisted_at,
        TokenBlacklist.expires_at
    ]


    # Default sort (newest first)
    column_default_sort = [(TokenBlacklist.blacklisted_at, True)]

    # Detail view - TAMPILKAN SEMUA!
    column_details_list = [
        TokenBlacklist.id,
        TokenBlacklist.user_id,
        TokenBlacklist.token,
        TokenBlacklist.blacklisted_at,
        TokenBlacklist.expires_at
    ]

    # Exclude from form (read-only table)
    form_excluded_columns = [
        TokenBlacklist.blacklisted_at
    ]

    # Labels
    column_labels = {
        TokenBlacklist.id: "ID",
        TokenBlacklist.user_id: "User ID",
        TokenBlacklist.token: "Token (JWT)",
        TokenBlacklist.blacklisted_at: "Blacklisted At",
        TokenBlacklist.expires_at: "Expires At"
    }

    # Formatters
    column_formatters = {
        TokenBlacklist.token: lambda m, a: f"{m.token[:20]}...{m.token[-20:]}" if len(m.token) > 40 else m.token
    }

    # Disable create/edit (only view/delete)
    can_create = False
    can_edit = False


# -----------------------------
# Setup Admin Panel
# -----------------------------
def setup_admin(app, engine):
    from app.core.admin_auth import AdminAuth

    admin = Admin(
        app=app,
        engine=engine,
        title="DR Detection Admin Panel",
        base_url="/admin",
        authentication_backend=AdminAuth(secret_key=settings.ADMIN_SECRET_KEY),
        templates_dir="app/templates/admin"
    )

    # Add all views
    admin.add_view(UserAdmin)
    admin.add_view(PatientAdmin)
    admin.add_view(FundusImageAdmin)
    admin.add_view(DetectionAdmin)
    admin.add_view(TokenBlacklistAdmin)  # ← NEW!

    return admin