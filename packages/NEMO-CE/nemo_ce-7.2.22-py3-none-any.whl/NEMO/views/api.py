import mimetypes
import platform
from importlib import metadata
from urllib.parse import unquote

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import default_storage
from django.db import transaction
from django.http import FileResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound
from django.utils.safestring import mark_safe
from drf_excel.mixins import XLSXFileMixin
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.serializers import ListSerializer
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from NEMO.models import (
    Account,
    AccountType,
    AdjustmentRequest,
    Alert,
    AlertCategory,
    Area,
    AreaAccessRecord,
    BuddyRequest,
    Comment,
    Configuration,
    ConfigurationOption,
    ConfigurationPrecursor,
    ConfigurationPrecursorSchedule,
    ConfigurationPrecursorSlot,
    Consumable,
    ConsumableCategory,
    ConsumableWithdraw,
    Customization,
    Interlock,
    InterlockCard,
    InterlockCardCategory,
    PhysicalAccessLevel,
    Project,
    ProjectDiscipline,
    ProjectType,
    Qualification,
    QualificationLevel,
    RecurringConsumableCharge,
    Reservation,
    Resource,
    ScheduledOutage,
    StaffAssistanceRequest,
    StaffCharge,
    Task,
    TemporaryPhysicalAccessRequest,
    Tool,
    ToolCredentials,
    TrainingEvent,
    TrainingSession,
    TrainingTechnique,
    UsageEvent,
    User,
    UserDocuments,
    UserPreferences,
)
from NEMO.rest_pagination import NEMOPageNumberPagination
from NEMO.serializers import (
    AccountSerializer,
    AccountTypeSerializer,
    AdjustmentRequestSerializer,
    AlertCategorySerializer,
    AlertSerializer,
    AreaAccessRecordSerializer,
    AreaSerializer,
    BillableItemSerializer,
    BuddyRequestSerializer,
    ConfigurationOptionSerializer,
    ConfigurationPrecursorScheduleSerializer,
    ConfigurationPrecursorSerializer,
    ConfigurationPrecursorSlotSerializer,
    ConfigurationSerializer,
    ConsumableCategorySerializer,
    ConsumableSerializer,
    ConsumableWithdrawSerializer,
    ContentTypeSerializer,
    CustomizationSerializer,
    GroupSerializer,
    InterlockCardCategorySerializer,
    InterlockCardSerializer,
    InterlockSerializer,
    PermissionSerializer,
    PhysicalAccessLevelSerializer,
    ProjectDisciplineSerializer,
    ProjectSerializer,
    ProjectTypeSerializer,
    QualificationLevelSerializer,
    QualificationSerializer,
    RecurringConsumableChargeSerializer,
    ReservationSerializer,
    ResourceSerializer,
    ScheduledOutageSerializer,
    StaffAssistanceRequestSerializer,
    StaffChargeSerializer,
    TaskSerializer,
    TemporaryPhysicalAccessRequestSerializer,
    ToolCommentSerializer,
    ToolCredentialsSerializer,
    ToolSerializer,
    ToolStatusSerializer,
    TrainingEventSerializer,
    TrainingSessionSerializer,
    TrainingTechniqueSerializer,
    UsageEventSerializer,
    UserDocumentSerializer,
    UserPreferenceSerializer,
    UserSerializer,
)
from NEMO.templatetags.custom_tags_and_filters import app_version
from NEMO.typing import QuerySetType
from NEMO.utilities import export_format_datetime, load_properties_schemas, remove_duplicates
from NEMO.views.api_billing import (
    BillingFilterForm,
    get_billing_charges,
)
from NEMO.views.constants import MEDIA_PROTECTED
from NEMO.views.customization import ApplicationCustomization
from NEMO.views.qualifications import disqualify, qualify

date_filters = ["exact", "in", "month", "year", "day", "gte", "gt", "lte", "lt", "isnull"]
time_filters = ["exact", "in", "hour", "minute", "second", "gte", "gt", "lte", "lt", "isnull"]
datetime_filters = remove_duplicates(date_filters + time_filters + ["week"])
string_filters = ["exact", "iexact", "in", "contains", "icontains", "isempty"]
number_filters = ["exact", "in", "gte", "gt", "lte", "lt", "isnull"]
key_filters = ["exact", "in", "isnull"]
manykey_filters = ["exact", "isnull"]
boolean_filters = ["exact"]


class SingleInstanceHTMLFormBrowsableAPIRenderer(BrowsableAPIRenderer):
    """
    This implementation of the BrowsableAPIRenderer prevents it from throwing
    errors while a list of data is sent to bulk create items
    """

    def render_form_for_serializer(self, serializer):
        if isinstance(serializer, ListSerializer):
            return mark_safe("<p>Form rendering is not available when creating more than one item at a time</p>")
        else:
            return super().render_form_for_serializer(serializer)


class ModelViewSet(XLSXFileMixin, viewsets.ModelViewSet):
    """
    An extension of the model view set, which accepts a json list of objects
    to create multiple instances at once.
    Also allows XLSX retrieval
    """

    # Bypass pagination when exporting into any format that's not the browsable API
    def paginate_queryset(self, queryset):
        page_size_override = self.request and self.request.GET.get(NEMOPageNumberPagination.page_size_query_param, None)
        renderer = (
            self.request.accepted_renderer if self.request and hasattr(self.request, "accepted_renderer") else None
        )
        if page_size_override is not None or not renderer or isinstance(renderer, BrowsableAPIRenderer):
            return super().paginate_queryset(queryset)
        return None

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
        except Exception as e:
            raise ValidationError({"error": str(e)})
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, headers=headers)

    def get_renderers(self):
        # we need to disable the HTML form renderer when using Serializer with many=True
        new_renderers = []
        for renderer in self.renderer_classes:
            if isinstance(renderer(), BrowsableAPIRenderer):
                new_renderers.append(SingleInstanceHTMLFormBrowsableAPIRenderer())
            else:
                new_renderers.append(renderer())
        return new_renderers

    def get_filename(self, *args, **kwargs):
        return f"{self.filename}-{export_format_datetime()}.xlsx"


class AlertCategoryViewSet(viewsets.ModelViewSet):
    filename = "alert_categories"
    queryset = AlertCategory.objects.all()
    serializer_class = AlertCategorySerializer
    filterset_fields = {
        "id": key_filters,
        "name": string_filters,
    }


class AlertViewSet(ModelViewSet):
    filename = "alerts"
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    filterset_fields = {
        "id": key_filters,
        "title": string_filters,
        "category": string_filters,
        "contents": string_filters,
        "creation_time": datetime_filters,
        "creator": key_filters,
        "user": key_filters,
        "debut_time": datetime_filters,
        "expiration_time": datetime_filters,
        "dismissible": boolean_filters,
        "expired": boolean_filters,
        "deleted": boolean_filters,
    }


class UserViewSet(ModelViewSet):
    filename = "users"
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filterset_fields = {
        "id": key_filters,
        "type": key_filters,
        "domain": string_filters,
        "username": string_filters,
        "first_name": string_filters,
        "last_name": string_filters,
        "email": string_filters,
        "badge_number": string_filters,
        "is_active": boolean_filters,
        "is_staff": boolean_filters,
        "is_facility_manager": boolean_filters,
        "is_superuser": boolean_filters,
        "is_service_personnel": boolean_filters,
        "is_technician": boolean_filters,
        "training_required": boolean_filters,
        "date_joined": datetime_filters,
        "last_login": datetime_filters,
        "access_expiration": date_filters,
        "physical_access_levels": manykey_filters,
        "projects": manykey_filters,
    }


class UserDocumentsViewSet(ModelViewSet):
    filename = "user_documents"
    queryset = UserDocuments.objects.all()
    serializer_class = UserDocumentSerializer
    filterset_fields = {
        "id": key_filters,
        "user": key_filters,
        "name": string_filters,
        "url": string_filters,
        "display_order": number_filters,
        "uploaded_at": datetime_filters,
    }


class UserPreferencesViewSet(ModelViewSet):
    filename = "user_preferences"
    queryset = UserPreferences.objects.all()
    serializer_class = UserPreferenceSerializer
    filterset_fields = {
        "id": key_filters,
        "user": key_filters,
        "attach_created_reservation": boolean_filters,
        "attach_cancelled_reservation": boolean_filters,
        "display_new_buddy_request_notification": boolean_filters,
        "email_new_buddy_request_reply": boolean_filters,
        "email_new_adjustment_request_reply": boolean_filters,
        "staff_status_view": string_filters,
        "email_alternate": string_filters,
        "email_send_reservation_emails": number_filters,
        "email_send_buddy_request_replies": number_filters,
        "email_send_staff_assistance_request_replies": number_filters,
        "email_send_access_request_updates": number_filters,
        "email_send_adjustment_request_updates": number_filters,
        "email_send_broadcast_emails": number_filters,
        "email_send_task_updates": number_filters,
        "email_send_access_expiration_emails": number_filters,
        "email_send_tool_qualification_expiration_emails": number_filters,
        "email_send_wait_list_notification_emails": number_filters,
        "email_send_usage_reminders": number_filters,
        "email_send_reservation_reminders": number_filters,
        "email_send_reservation_ending_reminders": number_filters,
        "recurring_charges_reminder_days": string_filters,
        "create_reservation_confirmation_override": boolean_filters,
        "change_reservation_confirmation_override": boolean_filters,
        "email_send_recurring_charges_reminder_emails": number_filters,
        "tool_freed_time_notifications": manykey_filters,
        "tool_freed_time_notifications_min_time": number_filters,
        "tool_freed_time_notifications_max_future_days": number_filters,
        "tool_task_notifications": manykey_filters,
    }

    def create(self, request, *args, **kwargs):
        many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data.get("user")
        if not user:
            raise ValidationError({"user": "This field is required"})
        if UserPreferences.objects.filter(user=user).exists():
            raise ValidationError({"user": "This user already has preferences"})
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        prefs = serializer.save()
        user = serializer.validated_data.get("user")
        user.preferences_id = prefs.id
        user.save(update_fields=["preferences_id"])

    def perform_update(self, serializer):
        user = serializer.validated_data.get("user")
        current_user = self.get_object().user
        if user and user != current_user:
            raise ValidationError({"user": "Cannot change the user associated with these preferences"})
        return super().perform_update(serializer)


class ProjectDisciplineViewSet(ModelViewSet):
    filename = "project_disciplines"
    queryset = ProjectDiscipline.objects.all()
    serializer_class = ProjectDisciplineSerializer
    filterset_fields = {"id": key_filters, "name": string_filters, "display_order": number_filters}


class ProjectTypeViewSet(ModelViewSet):
    filename = "project_types"
    queryset = ProjectType.objects.all()
    serializer_class = ProjectTypeSerializer
    filterset_fields = {"id": key_filters, "name": string_filters, "display_order": number_filters}


class ProjectViewSet(ModelViewSet):
    filename = "projects"
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    filterset_fields = {
        "id": key_filters,
        "name": string_filters,
        "application_identifier": string_filters,
        "active": boolean_filters,
        "account_id": key_filters,
        "account": key_filters,
    }


class AccountTypeViewSet(ModelViewSet):
    filename = "account_types"
    queryset = AccountType.objects.all()
    serializer_class = AccountTypeSerializer
    filterset_fields = {"id": key_filters, "name": string_filters, "display_order": number_filters}


class AccountViewSet(ModelViewSet):
    filename = "accounts"
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    filterset_fields = {"id": key_filters, "name": string_filters, "active": boolean_filters}


class ToolViewSet(ModelViewSet):
    filename = "tools"
    queryset = Tool.objects.all()
    serializer_class = ToolSerializer
    filterset_fields = {
        "id": key_filters,
        "name": string_filters,
        "visible": boolean_filters,
        "_serial": string_filters,
        "_category": string_filters,
        "_operational": boolean_filters,
        "_location": string_filters,
        "_requires_area_access": key_filters,
        "_post_usage_questions": string_filters,
        "_pre_usage_questions": string_filters,
    }


class QualificationLevelViewSet(ModelViewSet):
    filename = "qualification_levels"
    queryset = QualificationLevel.objects.all()
    serializer_class = QualificationLevelSerializer
    filterset_fields = {
        "id": key_filters,
        "name": string_filters,
        "qualify_user": boolean_filters,
        "qualify_schedule": boolean_filters,
        "qualify_weekends": boolean_filters,
        "schedule_start_time": time_filters,
        "schedule_end_time": time_filters,
    }


class QualificationViewSet(ModelViewSet):
    filename = "qualifications"
    queryset = Qualification.objects.all()
    serializer_class = QualificationSerializer
    filterset_fields = {
        "id": key_filters,
        "user": key_filters,
        "tool": key_filters,
        "qualified_on": date_filters,
    }

    def get_serializer(self, *args, **kwargs):
        """Don't allow update on user or tool (POST ok)"""
        serializer = super().get_serializer(*args, **kwargs)
        if self.request.method == "PUT" or self.request.method == "PATCH":
            serializer.fields["user"].read_only = True
            serializer.fields["tool"].read_only = True
        # Remove qualification levels if we don't have any
        if (
            not QualificationLevel.objects.exists()
            and getattr(serializer, "fields", None)
            and "qualification_level" in serializer.fields
        ):
            del serializer.fields["qualification_level"]
        return serializer

    # Override create and update to set the user
    def create(self, request, *args, **kwargs):
        self.request_user = request.user
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self.request_user = request.user
        return super().update(request, *args, **kwargs)

    # Override create, update and destroy to use qualify/disqualify methods
    def perform_create(self, serializer):
        self.qualify(serializer)

    def perform_update(self, serializer):
        self.qualify(serializer)

    def qualify(self, serializer):
        datas = serializer.data if getattr(serializer, "many", False) else [serializer.data]
        for data in datas:
            tool = Tool.objects.get(pk=data["tool"])
            user = User.objects.get(pk=data["user"])
            qualification_level_id = data.get("qualification_level", None)
            qualify(self.request_user, tool, user, qualification_level_id)

    def destroy(self, request, *args, **kwargs):
        instance: Qualification = self.get_object()
        disqualify(request.user, instance.tool, instance.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AreaViewSet(ModelViewSet):
    filename = "areas"
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    filterset_fields = {
        "id": key_filters,
        "name": string_filters,
        "parent_area": key_filters,
        "category": string_filters,
        "requires_reservation": boolean_filters,
        "buddy_system_allowed": boolean_filters,
        "maximum_capacity": number_filters,
        "count_staff_in_occupancy": boolean_filters,
        "count_service_personnel_in_occupancy": boolean_filters,
    }


class ResourceViewSet(ModelViewSet):
    filename = "resources"
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    filterset_fields = {
        "id": key_filters,
        "name": string_filters,
        "available": boolean_filters,
        "fully_dependent_tools": manykey_filters,
        "partially_dependent_tools": manykey_filters,
        "dependent_areas": manykey_filters,
    }


class ConfigurationViewSet(ModelViewSet):
    filename = "configurations"
    queryset = Configuration.objects.all()
    serializer_class = ConfigurationSerializer
    filterset_fields = {
        "id": key_filters,
        "name": string_filters,
        "tool_id": key_filters,
        "tool": key_filters,
        "advance_notice_limit": number_filters,
        "display_order": number_filters,
        "maintainers": manykey_filters,
        "qualified_users_are_maintainers": boolean_filters,
        "exclude_from_configuration_agenda": boolean_filters,
        "enabled": boolean_filters,
    }


class ConfigurationPrecursorViewSet(ModelViewSet):
    filename = "configuration_precursors"
    queryset = ConfigurationPrecursor.objects.all()
    serializer_class = ConfigurationPrecursorSerializer
    filterset_fields = {
        "id": key_filters,
        "name": string_filters,
        "tool_id": key_filters,
        "tool": key_filters,
        "advance_notice_limit": number_filters,
        "display_order": number_filters,
        "maintainers": manykey_filters,
        "qualified_users_are_maintainers": boolean_filters,
        "exclude_from_configuration_agenda": boolean_filters,
        "enabled": boolean_filters,
    }


class ConfigurationPrecursorSlotViewSet(ModelViewSet):
    filename = "configuration_precursor_slots"
    queryset = ConfigurationPrecursorSlot.objects.all()
    serializer_class = ConfigurationPrecursorSlotSerializer
    filterset_fields = {
        "id": key_filters,
        "precursor_configuration": key_filters,
        "schedule": key_filters,
        "setting": string_filters,
        "position": number_filters,
        "permanent_position": boolean_filters,
        "permanent_setting": boolean_filters,
    }


class ConfigurationPrecursorScheduleViewSet(ModelViewSet):
    filename = "configuration_precursor_schedules"
    queryset = ConfigurationPrecursorSchedule.objects.all()
    serializer_class = ConfigurationPrecursorScheduleSerializer
    filterset_fields = {
        "id": key_filters,
        "reset_time": ["exact", "gte", "gt", "lte", "lt"],
        "monday": boolean_filters,
        "tuesday": boolean_filters,
        "wednesday": boolean_filters,
        "thursday": boolean_filters,
        "friday": boolean_filters,
        "saturday": boolean_filters,
        "sunday": boolean_filters,
    }


class ConfigurationOptionViewSet(ModelViewSet):
    filename = "reservation_configuration_options"
    queryset = ConfigurationOption.objects.all()
    serializer_class = ConfigurationOptionSerializer
    filterset_fields = {
        "id": key_filters,
        "name": string_filters,
        "reservation_id": key_filters,
        "reservation": key_filters,
        "configuration_id": key_filters,
        "configuration": key_filters,
        "precursor_configuration": key_filters,
        "precursor_configuration_id": key_filters,
        "current_setting": string_filters,
        "current_position": number_filters,
        "locked": boolean_filters,
    }


class RecurringConsumableChargesViewSet(ModelViewSet):
    filename = "recurring_consumable_charges"
    queryset = RecurringConsumableCharge.objects.all()
    serializer_class = RecurringConsumableChargeSerializer
    filterset_fields = {
        "id": key_filters,
        "customer_id": key_filters,
        "customer": key_filters,
        "consumable_id": key_filters,
        "consumable": key_filters,
        "project_id": key_filters,
        "project": key_filters,
        "quantity": number_filters,
        "last_charge": datetime_filters,
        "rec_start": date_filters,
        "rec_frequency": number_filters,
        "rec_interval": number_filters,
        "rec_until": date_filters,
        "rec_count": number_filters,
        "last_updated": datetime_filters,
        "last_updated_by": key_filters,
        "last_updated_by_id": key_filters,
    }


class ReservationViewSet(ModelViewSet):
    filename = "reservations"
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    filterset_fields = {
        "id": key_filters,
        "start": datetime_filters,
        "end": datetime_filters,
        "project_id": key_filters,
        "project": key_filters,
        "user_id": key_filters,
        "user": key_filters,
        "creator_id": key_filters,
        "creator": key_filters,
        "tool_id": key_filters,
        "tool": key_filters,
        "area_id": key_filters,
        "area": key_filters,
        "question_data": string_filters,
        "cancelled": boolean_filters,
        "shortened": boolean_filters,
        "missed": boolean_filters,
        "validated": boolean_filters,
        "validated_by": key_filters,
        "waived": boolean_filters,
        "waived_on": datetime_filters,
        "waived_by": key_filters,
    }


class UsageEventViewSet(ModelViewSet):
    filename = "usage_events"
    queryset = UsageEvent.objects.all()
    serializer_class = UsageEventSerializer
    filterset_fields = {
        "id": key_filters,
        "start": datetime_filters,
        "end": datetime_filters,
        "project_id": key_filters,
        "project": key_filters,
        "user_id": key_filters,
        "user": key_filters,
        "operator_id": key_filters,
        "operator": key_filters,
        "tool_id": key_filters,
        "tool": key_filters,
        "training": boolean_filters,
        "validated": boolean_filters,
        "validated_by": key_filters,
        "waived": boolean_filters,
        "waived_on": datetime_filters,
        "waived_by": key_filters,
    }


class AreaAccessRecordViewSet(ModelViewSet):
    filename = "area_access_records"
    queryset = AreaAccessRecord.objects.all().order_by("-start")
    serializer_class = AreaAccessRecordSerializer
    filterset_fields = {
        "id": key_filters,
        "start": datetime_filters,
        "end": datetime_filters,
        "project_id": key_filters,
        "project": key_filters,
        "customer_id": key_filters,
        "customer": key_filters,
        "area_id": key_filters,
        "area": key_filters,
        "staff_charge_id": key_filters,
        "staff_charge": key_filters,
        "validated": boolean_filters,
        "validated_by": key_filters,
        "waived": boolean_filters,
        "waived_on": datetime_filters,
        "waived_by": key_filters,
    }


class TaskViewSet(ModelViewSet):
    filename = "tasks"
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filterset_fields = {
        "id": key_filters,
        "urgency": number_filters,
        "tool_id": key_filters,
        "tool": key_filters,
        "force_shutdown": boolean_filters,
        "safety_hazard": boolean_filters,
        "creator_id": key_filters,
        "creator": key_filters,
        "creation_time": datetime_filters,
        "estimated_resolution_time": datetime_filters,
        "problem_category": key_filters,
        "cancelled": boolean_filters,
        "resolved": boolean_filters,
        "resolution_time": datetime_filters,
        "resolver_id": key_filters,
        "resolver": key_filters,
        "resolution_category": key_filters,
    }


class ScheduledOutageViewSet(ModelViewSet):
    filename = "outages"
    queryset = ScheduledOutage.objects.all()
    serializer_class = ScheduledOutageSerializer
    filterset_fields = {
        "id": key_filters,
        "start": datetime_filters,
        "end": datetime_filters,
        "creator_id": key_filters,
        "creator": key_filters,
        "category": string_filters,
        "tool_id": key_filters,
        "tool": key_filters,
        "area_id": key_filters,
        "area": key_filters,
        "resource_id": key_filters,
        "resource": key_filters,
    }


class StaffChargeViewSet(ModelViewSet):
    filename = "staff_charges"
    queryset = StaffCharge.objects.all()
    serializer_class = StaffChargeSerializer
    filterset_fields = {
        "id": key_filters,
        "staff_member_id": key_filters,
        "staff_member": key_filters,
        "customer_id": key_filters,
        "customer": key_filters,
        "project_id": key_filters,
        "project": key_filters,
        "start": datetime_filters,
        "end": datetime_filters,
        "note": string_filters,
        "validated": boolean_filters,
        "validated_by": key_filters,
        "waived": boolean_filters,
        "waived_on": datetime_filters,
        "waived_by": key_filters,
    }


class TrainingEventViewSet(ModelViewSet):
    filename = "training_event"
    queryset = TrainingEvent.objects.all()
    serializer_class = TrainingEventSerializer
    filterset_fields = {
        "id": key_filters,
        "creation_time": datetime_filters,
        "start": datetime_filters,
        "end": datetime_filters,
        "message": string_filters,
        "capacity": number_filters,
        "cancelled": boolean_filters,
        "cancellation_time": datetime_filters,
        "cancellation_reason": string_filters,
        "cancelled_by_id": key_filters,
        "cancelled_by": key_filters,
        "creator_id": key_filters,
        "creator": key_filters,
        "technique_id": key_filters,
        "technique": key_filters,
        "tool_id": key_filters,
        "tool": key_filters,
        "trainer_id": key_filters,
        "trainer": key_filters,
        "recorded": boolean_filters,
        "invitation_only": boolean_filters,
        "auto_cancel": datetime_filters,
    }


class TrainingSessionViewSet(ModelViewSet):
    filename = "training_sessions"
    queryset = TrainingSession.objects.all()
    serializer_class = TrainingSessionSerializer
    filterset_fields = {
        "id": key_filters,
        "trainer_id": key_filters,
        "trainer": key_filters,
        "trainee_id": key_filters,
        "trainee": key_filters,
        "tool_id": key_filters,
        "tool": key_filters,
        "project_id": key_filters,
        "project": key_filters,
        "usage_event_id": key_filters,
        "usage_event": key_filters,
        "duration": number_filters,
        "type": number_filters,
        "date": datetime_filters,
        "qualified": boolean_filters,
        "validated": boolean_filters,
        "validated_by": key_filters,
        "waived": boolean_filters,
        "waived_on": datetime_filters,
        "waived_by": key_filters,
    }


class TrainingTechniqueViewSet(ModelViewSet):
    filename = "training_techniquess"
    queryset = TrainingTechnique.objects.all()
    serializer_class = TrainingTechniqueSerializer
    filterset_fields = {
        "id": key_filters,
        "name": string_filters,
    }


class ConsumableCategoryViewSet(ModelViewSet):
    filename = "consumable_categories"
    queryset = ConsumableCategory.objects.all()
    serializer_class = ConsumableCategorySerializer
    filterset_fields = {"id": key_filters, "name": string_filters}


class ConsumableViewSet(ModelViewSet):
    filename = "consumables"
    queryset = Consumable.objects.all()
    serializer_class = ConsumableSerializer
    filterset_fields = {
        "id": key_filters,
        "category_id": key_filters,
        "category": key_filters,
        "quantity": number_filters,
        "reminder_threshold": number_filters,
        "visible": boolean_filters,
        "reusable": boolean_filters,
        "reminder_threshold_reached": boolean_filters,
    }


class ConsumableWithdrawViewSet(ModelViewSet):
    filename = "consumable_withdrawals"
    queryset = ConsumableWithdraw.objects.all()
    serializer_class = ConsumableWithdrawSerializer
    filterset_fields = {
        "id": key_filters,
        "customer_id": key_filters,
        "customer": key_filters,
        "merchant_id": key_filters,
        "merchant": key_filters,
        "consumable_id": key_filters,
        "consumable": key_filters,
        "project_id": key_filters,
        "project": key_filters,
        "quantity": number_filters,
        "date": datetime_filters,
        "validated": boolean_filters,
        "validated_by": key_filters,
        "waived": boolean_filters,
        "waived_on": datetime_filters,
        "waived_by": key_filters,
    }


class ContentTypeViewSet(XLSXFileMixin, viewsets.ReadOnlyModelViewSet):
    filename = "content_types"
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer
    pagination_class = None
    filterset_fields = {
        "id": key_filters,
        "app_label": string_filters,
        "model": string_filters,
    }

    def get_filename(self, *args, **kwargs):
        return f"{self.filename}-{export_format_datetime()}.xlsx"


class CustomizationViewSet(ModelViewSet):
    filename = "customizations"
    queryset = Customization.objects.all()
    serializer_class = CustomizationSerializer
    filterset_fields = {
        "name": string_filters,
        "value": string_filters,
    }


class InterlockCardCategoryViewSet(ModelViewSet):
    filename = "interlock_card_categories"
    queryset = InterlockCardCategory.objects.all()
    serializer_class = InterlockCardCategorySerializer
    filterset_fields = {
        "id": key_filters,
        "name": string_filters,
        "key": string_filters,
    }


class InterlockCardViewSet(ModelViewSet):
    filename = "interlock_cards"
    queryset = InterlockCard.objects.all()
    serializer_class = InterlockCardSerializer
    filterset_fields = {
        "id": key_filters,
        "name": string_filters,
        "server": string_filters,
        "number": number_filters,
        "even_port": number_filters,
        "odd_port": number_filters,
        "category": key_filters,
        "enabled": boolean_filters,
    }


class InterlockViewSet(ModelViewSet):
    filename = "interlocks"
    queryset = Interlock.objects.all()
    serializer_class = InterlockSerializer
    filterset_fields = {
        "id": key_filters,
        "card": key_filters,
        "channel": number_filters,
        "unit_id": number_filters,
        "state": number_filters,
        "most_recent_reply_time": datetime_filters,
    }


class PhysicalAccessLevelViewSet(ModelViewSet):
    filename = "physical_access_levels"
    queryset = PhysicalAccessLevel.objects.all()
    serializer_class = PhysicalAccessLevelSerializer
    filterset_fields = {
        "id": key_filters,
        "name": string_filters,
        "area": key_filters,
        "schedule": number_filters,
        "weekdays_start_time": time_filters,
        "weekdays_end_time": time_filters,
        "allow_staff_access": boolean_filters,
        "allow_user_request": boolean_filters,
    }


class BuddyRequestViewSet(ModelViewSet):
    filename = "buddy_requests"
    queryset = BuddyRequest.objects.all()
    serializer_class = BuddyRequestSerializer
    filterset_fields = {
        "id": key_filters,
        "creation_time": datetime_filters,
        "start": date_filters,
        "end": date_filters,
        "description": string_filters,
        "area": key_filters,
        "user": key_filters,
        "expired": boolean_filters,
        "deleted": boolean_filters,
    }


class TemporaryPhysicalAccessRequestViewSet(ModelViewSet):
    filename = "physical_access_requests"
    queryset = TemporaryPhysicalAccessRequest.objects.all()
    serializer_class = TemporaryPhysicalAccessRequestSerializer
    filterset_fields = {
        "id": key_filters,
        "creation_time": datetime_filters,
        "creator": key_filters,
        "last_updated": datetime_filters,
        "last_updated_by": key_filters,
        "physical_access_level": key_filters,
        "description": string_filters,
        "start_time": datetime_filters,
        "end_time": datetime_filters,
        "other_users": manykey_filters,
        "status": number_filters,
        "reviewer": key_filters,
        "deleted": boolean_filters,
    }


class AdjustmentRequestViewSet(ModelViewSet):
    filename = "adjustment_requests"
    queryset = AdjustmentRequest.objects.all()
    serializer_class = AdjustmentRequestSerializer
    filterset_fields = {
        "id": key_filters,
        "creation_time": datetime_filters,
        "creator": key_filters,
        "last_updated": datetime_filters,
        "last_updated_by": key_filters,
        "item_type": key_filters,
        "item_id": number_filters,
        "description": string_filters,
        "manager_note": string_filters,
        "new_start": datetime_filters,
        "new_end": datetime_filters,
        "status": number_filters,
        "reviewer": key_filters,
        "applied": boolean_filters,
        "applied_by": key_filters,
        "deleted": boolean_filters,
    }


class ToolCredentialsViewSet(ModelViewSet):
    filename = "tool_credentials"
    queryset = ToolCredentials.objects.all()
    serializer_class = ToolCredentialsSerializer
    filterset_fields = {
        "id": key_filters,
        "tool": key_filters,
        "username": string_filters,
        "password": string_filters,
        "comments": string_filters,
        "authorized_staff": manykey_filters,
    }


class ToolCommentViewSet(ModelViewSet):
    filename = "tool_comments"
    queryset = Comment.objects.all()
    serializer_class = ToolCommentSerializer
    filterset_fields = {
        "id": key_filters,
        "tool": key_filters,
        "author": key_filters,
        "creation_date": datetime_filters,
        "expiration_date": datetime_filters,
        "visible": boolean_filters,
        "hide_date": datetime_filters,
        "hidden_by": key_filters,
        "content": string_filters,
        "staff_only": boolean_filters,
        "pinned": boolean_filters,
    }


class StaffAssistanceRequestViewSet(ModelViewSet):
    filename = "staff_assistance_requests"
    queryset = StaffAssistanceRequest.objects.all()
    serializer_class = StaffAssistanceRequestSerializer
    filterset_fields = {
        "id": key_filters,
        "user": key_filters,
        "creation_time": datetime_filters,
        "description": string_filters,
        "resolved": boolean_filters,
        "deleted": boolean_filters,
    }


class GroupViewSet(ModelViewSet):
    filename = "groups"
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    filterset_fields = {
        "name": string_filters,
        "permissions": manykey_filters,
    }


# Should not be able to edit permissions
class PermissionViewSet(XLSXFileMixin, viewsets.ReadOnlyModelViewSet):
    filename = "permissions"
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    pagination_class = None
    filterset_fields = {
        "name": string_filters,
        "codename": string_filters,
        "content_type_id": key_filters,
        "content_type": key_filters,
    }

    def get_filename(self, *args, **kwargs):
        return f"{self.filename}-{export_format_datetime()}.xlsx"


class BillingViewSet(XLSXFileMixin, viewsets.GenericViewSet):
    serializer_class = BillableItemSerializer

    def list(self, request, *args, **kwargs):
        billing_form = BillingFilterForm(self.request.GET)
        if not billing_form.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=billing_form.errors)
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def check_permissions(self, request):
        if not request or not request.user.has_perm("NEMO.use_billing_api"):
            self.permission_denied(request)

    def get_queryset(self):
        return get_billing_charges(self.request.GET)

    def get_filename(self, *args, **kwargs):
        return f"billing-{export_format_datetime()}.xlsx"


class ToolStatusViewSet(XLSXFileMixin, viewsets.GenericViewSet):
    serializer_class = ToolStatusSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def check_permissions(self, request):
        if not request or not request.user.has_perm("NEMO.view_tool"):
            self.permission_denied(request)

    def get_queryset(self) -> QuerySetType[Tool]:
        tools: QuerySetType[Tool] = Tool.objects.all()
        for tool in tools:
            pbs = tool.problems()
            outages = tool.scheduled_outages()
            partial_outages = tool.scheduled_partial_outages()
            rss_unavailable = tool.unavailable_required_resources()
            partial_rss_unavailable = tool.unavailable_nonrequired_resources()
            tool.problem_descriptions = ", ".join(pb.problem_description for pb in pbs) if pbs else None
            tool.outages = ", ".join(outage.title for outage in outages) if outages else None
            tool.partial_outages = ", ".join(outage.title for outage in partial_outages) if partial_outages else None
            tool.required_resources_unavailable = (
                ", ".join(res.name for res in rss_unavailable) if rss_unavailable else None
            )
            tool.optional_resources_unavailable = (
                ", ".join(res.name for res in partial_rss_unavailable) if partial_rss_unavailable else None
            )
        return tools

    def get_filename(self, *args, **kwargs):
        return f"tool_status-{export_format_datetime()}.xlsx"


class MetadataViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        metadata_dict = get_app_metadata()
        metadata_dict["authenticators"] = [
            authenticator.__class__.__name__ for authenticator in self.get_authenticators()
        ]
        return Response(metadata_dict)


def get_app_metadata():
    nemo_packages = []
    other_packages = []

    for package in metadata.distributions():
        package_name = package.metadata["name"]
        package_version = package.metadata["version"]
        if package_name.lower().startswith("nemo"):
            nemo_packages.append(f"{package_name}=={package_version}")
        else:
            other_packages.append(f"{package_name}=={package_version}")
    return {
        "nemo_version": app_version(),
        "python_version": platform.python_version(),
        "os_version": platform.platform(),
        "site_title": ApplicationCustomization.get("site_title"),
        "facility_name": ApplicationCustomization.get("facility_name"),
        "nemo_plugins": nemo_packages,
        "other_packages": other_packages,
        "json_properties_schemas": {"tool": load_properties_schemas("Tool")},
    }


class MediaAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, path, *args, **kwargs):
        clean_path = unquote(path)
        user: User = request.user
        if clean_path.startswith(MEDIA_PROTECTED) and not user.is_any_part_of_staff:
            return HttpResponseForbidden()
        if not clean_path or not default_storage.exists(clean_path):
            return HttpResponseNotFound()
        # Guess the MIME type of the media file from its extension.
        # This is good enough since those files are ours, and we typically use the correct extensions.
        mimetype, encoding = mimetypes.guess_type(path, strict=True)
        if not mimetype:
            return HttpResponseBadRequest()
        return FileResponse(default_storage.open(clean_path), content_type=mimetype)
