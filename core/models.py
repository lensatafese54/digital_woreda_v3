import datetime
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class BirthRegistration(models.Model):
    # Choice Enums
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending / ተጠባባቂ'
        APPROVED = 'APPROVED', 'Approved / የፀደቀ'
        REJECTED = 'REJECTED', 'Rejected / የተከለከለ'

    class Sex(models.TextChoices):
        MALE = 'MALE', 'Male / ወንድ'
        FEMALE = 'FEMALE', 'Female / ሴት'

    # Child Information
    child_full_name_amharic = models.CharField(max_length=200, verbose_name="Child Name (Amharic)")
    child_full_name_english = models.CharField(max_length=200, verbose_name="Child Name (English)")
    sex = models.CharField(
        max_length=10, 
        choices=Sex.choices,
        verbose_name="Sex"
    )
    birth_day = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        verbose_name="Birth Day"
    )
    birth_month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(13)],
        verbose_name="Birth Month (EC)"
    )
    birth_year_ec = models.IntegerField(verbose_name="Birth Year (EC)")
    birth_year_gc = models.IntegerField(verbose_name="Birth Year (GC)")
    subcity = models.CharField(max_length=100, db_index=True, verbose_name="Subcity")
    woreda = models.CharField(max_length=50, verbose_name="Woreda")
    hospital_org_name = models.CharField(max_length=200, verbose_name="Hospital/Organization")

    # Parents Information
    father_name_amharic = models.CharField(max_length=200, verbose_name="Father Name (Amharic)")
    father_name_english = models.CharField(max_length=200, verbose_name="Father Name (English)")
    mother_name_amharic = models.CharField(max_length=200, verbose_name="Mother Name (Amharic)")
    mother_name_english = models.CharField(max_length=200, verbose_name="Mother Name (English)")

    # Applicant / Declarant Information
    applicant_name_amharic = models.CharField(max_length=200, blank=True, null=True, verbose_name="Applicant Name (Amharic)")
    applicant_name_english = models.CharField(max_length=200, blank=True, null=True, verbose_name="Applicant Name (English)")
    applicant_relation = models.CharField(max_length=100, blank=True, null=True, verbose_name="Applicant Relation")
    applicant_age = models.IntegerField(
        blank=True, 
        null=True, 
        validators=[MinValueValidator(18), MaxValueValidator(120)],
        verbose_name="Applicant Age"
    )
    applicant_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Applicant Phone")

    # File & Photo Uploads
    child_photo = models.ImageField(upload_to='photos/children/%Y/%m/', blank=True, null=True)
    father_photo = models.ImageField(upload_to='photos/fathers/%Y/%m/', blank=True, null=True)
    mother_photo = models.ImageField(upload_to='photos/mothers/%Y/%m/', blank=True, null=True)
    hospital_document = models.FileField(upload_to='documents/hospitals/%Y/%m/', blank=True, null=True)

    # Status & Administrative Audit
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.PENDING,
        db_index=True,
        verbose_name="Registration Status"
    )
    rejection_reason = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Rejection Reason",
        help_text="Detailed explanation provided to the applicant if status is REJECTED."
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Birth Registration"
        verbose_name_plural = "Birth Registrations"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['subcity', 'woreda']),
        ]

    def __str__(self):
        return f"{self.child_full_name_amharic} - ID: {self.formatted_id}"

    def clean(self):
        """Custom validations for Ethiopian Calendar parameters and administrative logic."""
        super().clean()

        # Ethiopian Month 13 (Pagume) validation: Cannot exceed 6 days
        if self.birth_month == 13 and self.birth_day > 6:
            raise ValidationError({
                'birth_day': "13ኛ ወር (ጳጉሜ) ከ 6 ቀን በላይ መሆን አይችልም / Month 13 (Pagumē) cannot exceed 6 days."
            })

        # Rejection reason constraint validation
        if self.status == self.Status.REJECTED and not self.rejection_reason:
            raise ValidationError({
                'rejection_reason': "ውድቅ የተደረገበት ምክንያት መገለጽ አለበት / A rejection reason must be provided when status is REJECTED."
            })

    @property
    def formatted_id(self):
        """Returns standard civil registry formatted registration number."""
        return f"CRRSA-{self.pk:05d}" if self.pk else "CRRSA-NEW"

    @property
    def full_location(self):
        """Returns standard subcity and woreda layout string."""
        return f"{self.subcity} Subcity, Woreda {self.woreda}"

    @property
    def child_display_name(self):
        """Bilingual format helper for UI rendering."""
        return f"{self.child_full_name_amharic} ({self.child_full_name_english})"

    @property
    def is_approved(self):
        return self.status == self.Status.APPROVED