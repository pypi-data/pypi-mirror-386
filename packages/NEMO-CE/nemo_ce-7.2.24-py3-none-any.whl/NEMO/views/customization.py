import time
from abc import ABC
from datetime import date, datetime
from logging import getLogger
from threading import Lock
from typing import Dict, Iterable, List, Optional

from dateutil.relativedelta import relativedelta
from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.validators import (
    validate_comma_separated_integer_list,
    validate_email,
    validate_integer,
)
from django.http import HttpResponseNotFound
from django.shortcuts import redirect, render
from django.template import Context, Template, TemplateDoesNotExist
from django.template.loader import get_template
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from NEMO.apps import init_admin_site
from NEMO.decorators import administrator_required, customization
from NEMO.exceptions import InvalidCustomizationException
from NEMO.models import (
    BadgeReader,
    ConsumableCategory,
    Customization,
    Notification,
    Project,
    RecurringConsumableCharge,
    Tool,
    TrainingSession,
    User,
    UserPreferences,
    UserType,
)
from NEMO.utilities import (
    RecurrenceFrequency,
    beginning_of_next_day,
    beginning_of_the_day,
    date_input_format,
    datetime_input_format,
    quiet_int,
)

customization_logger = getLogger(__name__)


class CustomizationBase(ABC):
    _instances = {}
    # Static cache variables
    _variables_cache = None
    _cache_expiry = 0
    _cache_lock = Lock()
    # Cache expiry time (in seconds, default 30 seconds)
    CACHE_TTL = quiet_int(getattr(settings, "CUSTOMIZATIONS_CACHE_SECONDS", 30), 30)

    # Here we can place variables that we need in NEMO but don't need to be set in UI
    variables = {"weekend_access_notification_last_sent": ""}
    files = []

    def __init__(self, key, title):
        self.key = key
        self.title = title

    @staticmethod
    def _load_cache():
        """
        Private method to load all variables into the cache from the database.
        Called when the cache is empty or expired.
        """
        with CustomizationBase._cache_lock:
            # Reload from the database only if the cache is empty or expired
            if CustomizationBase._variables_cache is None or time.time() > CustomizationBase._cache_expiry:
                # Load default values
                CustomizationBase._variables_cache = CustomizationBase._all_variables()
                # Then override with db values
                CustomizationBase._variables_cache.update(
                    {cust.name: cust.value for cust in Customization.objects.all()}
                )
                # Set the new cache expiration time
                CustomizationBase._cache_expiry = time.time() + CustomizationBase.CACHE_TTL

    @staticmethod
    def invalidate_cache():
        """
        Invalidate the cache immediately by clearing it.
        """
        with CustomizationBase._cache_lock:
            CustomizationBase._variables_cache = None
            CustomizationBase._cache_expiry = 0

    def template(self) -> Optional[str]:
        # We want to check if there is a customization template file in the app template dir
        # Otherwise we load it from the main template dir
        app = apps.get_containing_app_config(type(self).__module__)
        if app:
            for app_dir in [app.label, app.name, ""]:
                try:
                    template_path = f"{app_dir}{'/' if app_dir else ''}customizations/customizations_{self.key}.html"
                    get_template(template_path)  # will raise TemplateDoesNotExist if not found
                    return template_path
                except TemplateDoesNotExist:
                    pass
        customization_logger.debug(f"could not find any template for customization: {self.key}")

    def template_templates(self) -> Optional[str]:
        # We have a similar approach here except we are looking for a very specific file
        # named customizations_{key}_templates.html, and we are only looking in the app template dirs
        app = apps.get_containing_app_config(type(self).__module__)
        if app:
            for app_dir in [app.label, app.name, ""]:
                try:
                    template_path = (
                        f"{app_dir}{'/' if app_dir else ''}customizations/customizations_{self.key}_templates.html"
                    )
                    get_template(template_path)  # will raise TemplateDoesNotExist if it doesn't exist
                    return template_path
                except TemplateDoesNotExist:
                    pass

    def context(self) -> Dict:
        files_dict = {name: get_media_file_contents(name + extension) for name, extension in type(self).files}
        variables_dict = {name: type(self).get(name) for name in type(self).variables}
        return {"customization": self, **variables_dict, **files_dict}

    def save(self, request, element=None) -> Dict[str, Dict[str, str]]:
        errors = {}
        if element:
            # We are saving a file here
            item = None
            for name, extension in type(self).files:
                if name == element:
                    item = (name, extension)
                    break
            if item:
                store_media_file(request.FILES.get(element, ""), item[0] + item[1])
        else:
            # We are saving key values here
            for key in type(self).variables.keys():
                new_value = request.POST.get(key, "")
                try:
                    self.validate(key, new_value)
                    type(self).set(key, new_value)
                except (ValidationError, InvalidCustomizationException) as e:
                    errors[key] = {"error": str(e.message or e.msg), "value": new_value}
        return errors

    def validate(self, name, value):
        # This method is expected to throw a ValidationError when validation fails
        pass

    def validate_date(self, value):
        try:
            datetime.strptime(value, date_input_format)
        except ValueError as e:
            raise ValidationError(str(e))

    @staticmethod
    def add_instance(inst):
        CustomizationBase._instances[inst.key] = inst

    @staticmethod
    def instances() -> Iterable:
        return CustomizationBase._instances.values()

    @staticmethod
    def get_instance(key):
        return CustomizationBase._instances.get(key)

    @staticmethod
    def _all_variables() -> Dict:
        all_variables = CustomizationBase.variables
        for instance in CustomizationBase.instances():
            all_variables.update(instance.variables)
        return all_variables

    @classmethod
    def get(cls, name: str, raise_exception=True, use_cache=True) -> str:
        if name not in cls.variables:
            raise InvalidCustomizationException(name)
        default_value = cls.variables[name]
        if use_cache:
            # We are using the cache (default behavior)
            try:
                CustomizationBase._load_cache()  # Ensure cache is valid
                with CustomizationBase._cache_lock:
                    if name in CustomizationBase._variables_cache:
                        # Return the cached value
                        return CustomizationBase._variables_cache[name]
                    else:
                        # Return default value
                        return default_value
            except Exception:
                if raise_exception:
                    raise
                else:
                    return default_value
        else:
            # We are not using the cache, so we need to load the value from the database
            try:
                return Customization.objects.get(name=name).value
            except Customization.DoesNotExist:
                return default_value
            except Exception:
                if raise_exception:
                    raise
                else:
                    return default_value

    @staticmethod
    def get_all() -> Dict:
        """
        Retrieve all variables. Always reloading the cache.
        """
        CustomizationBase.invalidate_cache()  # Invalidate the cache
        CustomizationBase._load_cache()  # Ensure cache is valid
        return dict(CustomizationBase._variables_cache.copy().items())

    @classmethod
    def get_int(cls, name: str, default=None, raise_exception=True) -> int:
        return quiet_int(cls.get(name, raise_exception), default)

    @classmethod
    def get_bool(cls, name: str, raise_exception=True) -> bool:
        return cls.get(name, raise_exception) == "enabled"

    @classmethod
    def get_date(cls, name: str, raise_exception=True) -> date:
        str_date = cls.get(name, raise_exception)
        if str_date:
            return datetime.strptime(str_date, date_input_format).date()

    @classmethod
    def get_datetime(cls, name: str, raise_exception=True) -> datetime:
        str_datetime = cls.get(name, raise_exception)
        if str_datetime:
            return datetime.strptime(str_datetime, datetime_input_format)

    @classmethod
    def get_list(cls, name: str, raise_exception=True) -> List[str]:
        return [item.strip() for item in cls.get(name, raise_exception).split(",") if item]

    @classmethod
    def get_list_int(cls, name: str, raise_exception=True) -> List[int]:
        result = []
        for item in cls.get_list(name, raise_exception):
            if item:
                integer = quiet_int(item.strip(), None)
                if integer is not None:
                    result.append(integer)
        return result

    @classmethod
    def set(cls, name: str, value):
        if name not in cls.variables:
            raise InvalidCustomizationException(name, value)
        with CustomizationBase._cache_lock:
            if value:
                Customization.objects.update_or_create(name=name, defaults={"value": value})
            else:
                try:
                    Customization.objects.get(name=name).delete()
                except Customization.DoesNotExist:
                    pass
        # Invalidate the cache
        CustomizationBase.invalidate_cache()


@customization(key="application", title="Application")
class ApplicationCustomization(CustomizationBase):
    variables = {
        "facility_name": "Facility",
        "site_title": "NEMO-CE",
        "self_log_in": "",
        "self_log_out": "",
        "calendar_login_logout": "",
        "area_access_logout_already_logged_in": "",
        "area_access_open_door_on_logout": "",
        "show_badge_number": "",
        "default_badge_reader_id": "",
        "consumable_user_self_checkout": "",
        "consumable_category_collapse": "",
        "area_in_usage_reminders": "enabled",
        "calendar_page_title": "Calendar",
        "tool_control_page_title": "Tool control",
        "status_dashboard_page_title": "Status dashboard",
        "requests_page_title": "Requests",
        "safety_page_title": "Safety",
        "out_of_time_tool_send_to_abuse_email": "enabled",
        "out_of_time_area_send_to_abuse_email": "enabled",
        "kiosk_message": "<h1>Scan your badge to control tools</h1>",
        "kiosk_numpad_size": "large",
        "area_access_kiosk_option_login_success": "",
        "area_access_kiosk_option_logout_warning": "",
        "area_access_kiosk_option_already_logged_out": "",
    }

    def context(self) -> Dict:
        context_dict = super().context()
        context_dict["badge_readers"] = BadgeReader.objects.all()
        return context_dict

    def save(self, request, element=None):
        errors = super().save(request, element)
        init_admin_site()
        return errors


@customization(key="projects_and_accounts", title="Projects & accounts")
class ProjectsAccountsCustomization(CustomizationBase):
    variables = {
        "project_selection_template": "{{ project.name }}",
        "project_application_identifier_name": "Application identifier",
        "project_allow_document_upload": "",
        "account_list_active_only": "",
        "account_project_list_active_only": "",
        "project_list_active_only": "",
        "account_list_collapse": "",
        "project_allow_pi_manage_users": "",
        "project_allow_transferring_charges": "",
        "project_type_allow_multiple": "",
    }

    def validate(self, name, value):
        if name == "project_selection_template":
            try:
                Template(value).render(Context({"project": Project()}))
            except Exception as e:
                raise ValidationError(str(e))


@customization(key="user", title="User")
class UserCustomization(CustomizationBase):
    variables = {
        "default_user_training_not_required": "",
        "user_type_required": "",
        "user_list_active_only": "",
        "user_access_expiration_reminder_days": "",
        "user_access_expiration_reminder_cc": "",
        "user_access_expiration_buffer_days": "",
        "user_access_expiration_no_type": "",
        "user_access_expiration_types": "-1",
        "user_access_expiration_banner_warning": "",
        "user_access_expiration_banner_danger": "",
        "user_allow_document_upload": "",
        "user_allow_profile_view": "",
    }

    def context(self) -> Dict:
        context_dict = super().context()
        context_dict["user_types"] = UserType.objects.all()
        context_dict["user_access_expiration_types_list"] = self.get_list_int("user_access_expiration_types")
        return context_dict

    def validate(self, name, value):
        if name == "user_access_expiration_types" and value:
            validate_comma_separated_integer_list(value)
        if name == "user_access_expiration_buffer_days" and value:
            validate_integer(value)
        if name == "user_access_expiration_reminder_days" and value:
            # Check that we have an integer or a list of integers
            validate_comma_separated_integer_list(value)
        elif name == "user_access_expiration_reminder_cc":
            recipients = tuple([e for e in value.split(",") if e])
            for email in recipients:
                validate_email(email)

    def save(self, request, element=None) -> Dict[str, Dict[str, str]]:
        errors = super().save(request, element)

        user_types = ",".join(request.POST.getlist("user_access_expiration_types_list", []))
        try:
            self.validate("user_access_expiration_types", user_types)
            type(self).set("user_access_expiration_types", user_types)
        except (ValidationError, InvalidCustomizationException) as e:
            errors["user_access_expiration_types"] = {"error": str(e.message or e.msg), "value": user_types}
        return errors


@customization(key="emails", title="Email addresses")
class EmailsCustomization(CustomizationBase):
    variables = {
        "feedback_email_address": "",
        "user_office_email_address": "",
        "safety_email_address": "",
        "abuse_email_address": "",
    }

    def validate(self, name, value):
        validate_email(value)


@customization(key="calendar", title="Calendar")
class CalendarCustomization(CustomizationBase):
    variables = {
        "calendar_view": "agendaWeek",
        "calendar_first_day_of_week": "1",
        "calendar_axis_time_format": "ha",
        "calendar_day_column_format": "dddd MM/DD/YYYY",
        "calendar_day_time_format": "h:mm",
        "calendar_week_column_format": "ddd M/DD",
        "calendar_week_time_format": "h:mm",
        "calendar_month_column_format": "ddd",
        "calendar_month_time_format": "h(:mm)t",
        "calendar_start_of_the_day": "07:00:00",
        "calendar_now_indicator": "",
        "calendar_display_not_qualified_areas": "",
        "calendar_all_tools": "",
        "calendar_all_areas": "",
        "calendar_all_areastools": "",
        "calendar_outage_recurrence_limit": "90",
        "calendar_training_recurrence_limit": "90",
        "calendar_qualified_tools": "",
        "calendar_configuration_in_reservations": "",
        "calendar_status_bar_show_tool_reservation_policy": "enabled",
        "calendar_status_bar_show_tool_pinned_comments": "enabled",
        "calendar_status_bar_show_tool_latest_problem": "enabled",
        "calendar_status_bar_tool_max_width": "400",
        "create_reservation_confirmation": "",
        "change_reservation_confirmation": "",
        "reservation_confirmation_date_format": "MMMM D, yyyy",
        "reservation_confirmation_time_format": "h:mma",
    }

    @classmethod
    def set(cls, name: str, value):
        if name == "create_reservation_confirmation" or name == "change_reservation_confirmation":
            value_changed = value != cls.get(name)
            if value_changed:
                if name == "create_reservation_confirmation":
                    UserPreferences.objects.filter(create_reservation_confirmation_override=True).update(
                        create_reservation_confirmation_override=False
                    )
                elif name == "change_reservation_confirmation":
                    UserPreferences.objects.filter(change_reservation_confirmation_override=True).update(
                        change_reservation_confirmation_override=False
                    )
        super().set(name, value)


@customization(key="dashboard", title="Status dashboard")
class StatusDashboardCustomization(CustomizationBase):
    variables = {
        "dashboard_display_not_qualified_areas": "",
        "dashboard_hide_project": "",
        "dashboard_staff_status_first_day_of_week": "1",
        "dashboard_staff_status_staff_only": "",
        "dashboard_staff_status_weekdays_only": "",
        "dashboard_staff_status_date_format": "D m/d",
        "dashboard_staff_status_check_past_status": "",
        "dashboard_staff_status_check_future_status": "",
        "dashboard_staff_status_user_view": "",
        "dashboard_staff_status_staff_view": "",
        "dashboard_staff_status_absence_view_staff": "",
        "dashboard_staff_status_absence_view_user_office": "",
        "dashboard_staff_status_absence_view_accounting_officer": "",
        "dashboard_tool_sort": "name",
    }


@customization(key="interlock", title="Interlock")
class InterlockCustomization(CustomizationBase):
    variables = {
        "allow_bypass_interlock_on_failure": "",
        "tool_interlock_failure_message": "Communication with the interlock failed",
        "door_interlock_failure_message": "Communication with the interlock failed",
    }


@customization(key="shadowing_verification", title="Shadowing Verification")
class ShadowingVerificationCustomization(CustomizationBase):
    variables = {
        "shadowing_verification_request_title": "Shadowing Verifications",
        "shadowing_verification_request_display_max": "",
        "shadowing_verification_request_description_placeholder": "Please describe techniques used, processed, tool mode etc",
        "shadowing_verification_request_description": "",
    }


@customization(key="requests", title="User requests")
class UserRequestsCustomization(CustomizationBase):
    variables = {
        "buddy_requests_title": "Buddy requests board",
        "buddy_board_description": "",
        "staff_assistance_requests_enabled": "",
        "staff_assistance_requests_title": "Staff assistance requests",
        "staff_assistance_requests_description": "",
        "access_requests_title": "Access requests",
        "access_requests_description": "",
        "access_requests_minimum_users": "2",
        "access_requests_display_max": "",
        "weekend_access_notification_emails": "",
        "weekend_access_notification_cutoff_hour": "",
        "weekend_access_notification_cutoff_day": "",
    }

    def validate(self, name, value):
        if name == "weekend_access_notification_emails":
            recipients = tuple([e for e in value.split(",") if e])
            for email in recipients:
                validate_email(email)


@customization(key="adjustment_requests", title="Adjustment requests")
class AdjustmentRequestsCustomization(CustomizationBase):
    frequencies = [RecurrenceFrequency.DAILY, RecurrenceFrequency.WEEKLY, RecurrenceFrequency.MONTHLY]
    variables = {
        "adjustment_requests_enabled": "",
        "charges_validation_enabled": "",
        "adjustment_requests_tool_usage_enabled": "enabled",
        "adjustment_requests_area_access_enabled": "enabled",
        "adjustment_requests_missed_reservation_enabled": "enabled",
        "adjustment_requests_missed_reservation_times": "",
        "adjustment_requests_staff_staff_charges_enabled": "enabled",
        "adjustment_requests_consumable_withdrawal_enabled": "enabled",
        "adjustment_requests_consumable_withdrawal_self_checkout": "enabled",
        "adjustment_requests_consumable_withdrawal_staff_checkout": "enabled",
        "adjustment_requests_consumable_withdrawal_usage_event": "enabled",
        "adjustment_requests_waive_tool_usage_enabled": "",
        "adjustment_requests_waive_area_access_enabled": "",
        "adjustment_requests_waive_consumable_withdrawal_enabled": "",
        "adjustment_requests_waive_missed_reservation_enabled": "",
        "adjustment_requests_title": "Adjustment requests",
        "adjustment_requests_description": "",
        "adjustment_requests_charges_display_number": "10",
        "adjustment_requests_display_max": "",
        "adjustment_requests_time_limit_interval": "",
        "adjustment_requests_time_limit_frequency": "",
        "adjustment_requests_time_limit_monthly_cycle_day": "",
        "adjustment_requests_edit_charge_button": "",
        "adjustment_requests_apply_button": "",
    }

    @classmethod
    def get_date_limit(cls) -> Optional[datetime]:
        try:
            monthly_billing_day: int = cls.get_int("adjustment_requests_time_limit_monthly_cycle_day")
            interval = cls.get_int("adjustment_requests_time_limit_interval")
            freq = None
            if cls.get_int("adjustment_requests_time_limit_frequency"):
                freq = RecurrenceFrequency(cls.get_int("adjustment_requests_time_limit_frequency"))
            now_local = timezone.localtime()
            if interval and freq or monthly_billing_day:
                delta = relativedelta()
                if interval and freq:
                    delta = (
                        relativedelta(months=interval)
                        if freq == RecurrenceFrequency.MONTHLY
                        else (
                            relativedelta(weeks=interval)
                            if freq == RecurrenceFrequency.WEEKLY
                            else relativedelta(days=interval)
                        )
                    )
                period_cutoff = beginning_of_next_day(now_local - delta) if delta else None
                cycle_cutoff = None
                if monthly_billing_day:
                    if now_local.day > monthly_billing_day:
                        # After cutoff → return 1st of this month
                        cycle_cutoff = now_local.replace(day=1)
                    else:
                        # Before cutoff → return 1st of last month
                        cycle_cutoff = now_local.replace(day=1) - relativedelta(months=1)
                    cycle_cutoff = beginning_of_the_day(cycle_cutoff)
                if period_cutoff and cycle_cutoff:
                    return max(period_cutoff, cycle_cutoff)
                else:
                    return period_cutoff or cycle_cutoff
        except:
            pass

    @classmethod
    def are_adjustment_requests_enabled_for_user(cls, user: User) -> bool:
        adjustment_requests_enabled = cls.get("adjustment_requests_enabled")
        if adjustment_requests_enabled == "enabled":
            return True
        elif adjustment_requests_enabled == "reviewers_only":
            return user.is_adjustment_request_reviewer
        return False

    @classmethod
    def set(cls, name: str, value):
        if name == "adjustment_requests_enabled" and not value:
            # If adjustment requests are being disabled, remove all notifications
            previously_enabled = cls.get("adjustment_requests_enabled")
            if previously_enabled:
                Notification.objects.filter(
                    notification_type__in=[
                        Notification.Types.ADJUSTMENT_REQUEST,
                        Notification.Types.ADJUSTMENT_REQUEST_REPLY,
                    ]
                ).delete()
        super().set(name, value)

    def context(self) -> Dict:
        context_dict = super().context()
        context_dict["frequency_choices"] = [(freq.index, freq.display_value) for freq in self.frequencies]
        context_dict["date_limit"] = self.get_date_limit()
        return context_dict

    def validate(self, name, value):
        if value and name == "adjustment_requests_time_limit_frequency":
            try:
                if RecurrenceFrequency(int(value)) not in self.frequencies:
                    raise ValidationError(
                        f"frequency must be one of {[freq.display_value for freq in self.frequencies]}"
                    )
            except Exception as e:
                raise ValidationError(str(e))


@customization(key="recurring_charges", title="Recurring charges")
class RecurringChargesCustomization(CustomizationBase):
    variables = {
        "recurring_charges_name": "Recurring charges",
        "recurring_charges_lock": "",
        "recurring_charges_category": "",
        "recurring_charges_force_quantity": "",
        "recurring_charges_skip_customer_validation": "",
    }

    def __init__(self, key, title):
        super().__init__(key, title)
        self.update_title()

    def context(self) -> Dict:
        # Override to add list of consumable categories
        dictionary = super().context()
        dictionary["consumable_categories"] = ConsumableCategory.objects.all()
        return dictionary

    def update_title(self):
        self.title = self.get("recurring_charges_name", raise_exception=False, use_cache=False)
        meta_class = RecurringConsumableCharge._meta
        meta_class.verbose_name = self.title
        meta_class.verbose_name_plural = self.title if self.title.endswith("s") else self.title + "s"

    def save(self, request, element=None):
        errors = super().save(request, element)
        if not errors:
            self.update_title()
        return errors


@customization(key="tool", title="Tools")
class ToolCustomization(CustomizationBase):
    variables = {
        "tool_phone_number_required": "enabled",
        "tool_location_required": "enabled",
        "tool_task_updates_facility_managers": "enabled",
        "tool_task_updates_superusers": "",
        "tool_task_updates_allow_regular_user_preferences": "",
        "tool_control_hide_data_history_users": "",
        "tool_control_documents_in_separate_tab": "",
        "tool_control_configuration_setting_template": "{{ current_setting }}",
        "tool_control_ongoing_reservation_force_off": "",
        "tool_control_allow_take_over": "",
        "tool_control_broadcast_qualified_users": "",
        "tool_control_broadcast_upcoming_reservation": "",
        "tool_control_show_task_details": "",
        "tool_control_show_qualified_users_to_all": "",
        "tool_control_show_documents_only_qualified_users": "",
        "tool_control_show_tool_credentials": "enabled",
        "tool_control_show_next_reservation_user": "",
        "tool_control_prefill_post_usage_with_pre_usage_answers": "",
        "tool_control_use_self": "Use this tool for my own project",
        "tool_control_use_self_training": "Use this tool for my own project for training",
        "tool_control_use_for_other": "Use this tool on behalf of another user",
        "tool_control_use_for_other_training": "Use this tool on behalf of another user for training",
        "tool_control_use_for_other_remote": "Use this tool for a remote project",
        "tool_qualification_reminder_days": "",
        "tool_qualification_expiration_days": "",
        "tool_qualification_expiration_never_used_days": "",
        "tool_qualification_cc": "",
        "tool_problem_max_image_size_pixels": "750",
        "tool_problem_send_to_all_qualified_users": "",
        "tool_problem_allow_regular_user_preferences": "",
        "tool_problem_safety_hazard_automatic_shutdown": "",
        "tool_configuration_near_future_days": "1",
        "tool_reservation_policy_superusers_bypass": "",
        "tool_grant_access_emails": "",
        "tool_grant_access_include_physical_access": "",
        "tool_wait_list_spot_expiration": "15",
        "tool_wait_list_reservation_buffer": "15",
        "tool_freed_time_notification_include_username": "",
        "tool_freed_time_notify_next_reservation_enabled": "",
        "tool_freed_time_notify_next_reservation_min_freed_time": "15",
        "tool_freed_time_notify_next_reservation_starts_within": "1",
        "kiosk_only_show_qualified_tools": "",
    }

    def validate(self, name, value):
        if (
            name
            in [
                "tool_qualification_expiration_days",
                "tool_problem_max_image_size_pixels",
                "tool_configuration_near_future_days",
            ]
            and value
        ):
            validate_integer(value)
        if name == "tool_qualification_reminder_days" and value:
            # Check that we have an integer or a list of integers
            validate_comma_separated_integer_list(value)
        elif name == "tool_qualification_cc" or name == "tool_grant_access_emails":
            recipients = tuple([e for e in value.split(",") if e])
            for email in recipients:
                validate_email(email)
        if name == "tool_control_configuration_setting_template" and value:
            try:
                Template(value).render(Context({"current_setting": "setting"}))
            except Exception as e:
                raise ValidationError(str(e))


@customization(key="safety", title="Safety")
class SafetyCustomization(CustomizationBase):
    variables = {
        "safety_main_menu": "enabled",
        "safety_show_safety": "enabled",
        "safety_show_safety_issues": "enabled",
        "safety_show_safety_data_sheets": "enabled",
        "safety_data_sheets_keywords_default": "",
        "safety_items_expand_categories": "",
    }


@customization(key="knowledge_base", title="Knowledge base")
class KnowledgeBaseCustomization(CustomizationBase):
    variables = {
        "knowledge_base_user_expand_categories": "",
        "knowledge_base_staff_expand_categories": "",
    }


@customization(key="remote_work", title="Remote work")
class RemoteWorkCustomization(CustomizationBase):
    variables = {
        "remote_work_validation": "",
        "remote_work_start_area_access_automatically": "enabled",
        "remote_work_on_behalf_of_user": "always",
    }


@customization(key="training", title="Training")
class TrainingCustomization(CustomizationBase):
    variables = {
        "training_module_enabled": "enabled",
        "training_technique_empty_label": "Basic training",
        "training_request_default_availability_allowed": "",
        "training_request_default_message_required": "",
        "training_request_default_message_placeholder": "Add a message for the trainer",
        "training_event_default_auto_cancel": "",
        "training_event_default_duration": "",
        "training_event_default_capacity": "",
        "training_excluded_tools": "",
        "training_only_type": "",
        "training_allow_date": "",
        "training_included_hidden_tools": "",
        "training_show_in_user_requests": "",
        "training_upcoming_schedule_days": "7",
        "training_extra_email_addresses": "",
        "training_show_self_option_in_tool_control": "",
        "training_show_behalf_option_in_tool_control": "",
    }

    def context(self) -> Dict:
        # Override to add list of tools and training types
        dictionary = super().context()
        dictionary["tools"] = Tool.objects.all()
        dictionary["excluded_tools"] = Tool.objects.filter(id__in=self.get_list_int("training_excluded_tools"))
        dictionary["training_types"] = TrainingSession.Type.Choices
        dictionary["included_hidden_tools"] = Tool.objects.filter(
            id__in=self.get_list_int("training_included_hidden_tools")
        )
        return dictionary

    def validate(self, name, value):
        if (
            name
            in [
                "training_event_default_duration",
                "training_event_default_capacity",
                "training_event_default_auto_cancel",
            ]
            and value
        ):
            validate_integer(value)
        if name == "training_excluded_tools" and value:
            validate_comma_separated_integer_list(value)
        if name == "training_included_hidden_tools" and value:
            validate_comma_separated_integer_list(value)
        if name == "training_extra_email_addresses":
            recipients = tuple([e for e in value.split(",") if e])
            for email in recipients:
                validate_email(email)

    def save(self, request, element=None) -> Dict[str, Dict[str, str]]:
        errors = super().save(request, element)
        exclude_tools = ",".join(request.POST.getlist("training_excluded_tools_list", []))
        include_hidden_tools = ",".join(request.POST.getlist("training_included_hidden_tools_list", []))
        try:
            self.validate("training_excluded_tools", exclude_tools)
            type(self).set("training_excluded_tools", exclude_tools)
        except (ValidationError, InvalidCustomizationException) as e:
            errors["training_excluded_tools"] = {"error": str(e.message or e.msg), "value": exclude_tools}
        try:
            self.validate("training_included_hidden_tools", include_hidden_tools)
            type(self).set("training_included_hidden_tools", include_hidden_tools)
        except (ValidationError, InvalidCustomizationException) as e:
            errors["training_included_hidden_tools"] = {"error": str(e.message or e.msg), "value": include_hidden_tools}
        training_types = request.POST.getlist("training_type_list", [])
        if training_types and len(training_types) == 1:
            type(self).set("training_only_type", training_types[0])
        return errors

    @classmethod
    def set(cls, name: str, value):
        if name == "training_module_enabled" and value != "enabled":
            # If training is being disabled, remove all notifications
            previously_enabled = cls.get_bool("training_module_enabled")
            if previously_enabled:
                Notification.objects.filter(
                    notification_type__in=[
                        Notification.Types.TRAINING_INVITATION,
                        Notification.Types.TRAINING_REQUEST,
                        Notification.Types.TRAINING_ALL,
                    ]
                ).delete()
        super().set(name, value)


@customization(key="templates", title="File & email templates")
class TemplatesCustomization(CustomizationBase):
    files = [
        ("login_banner", ".html"),
        ("authorization_failed", ".html"),
        ("safety_introduction", ".html"),
        ("facility_rules_tutorial", ".html"),
        ("jumbotron_watermark", ".png"),
        ("access_request_notification_email", ".html"),
        ("adjustment_request_notification_email", ".html"),
        ("cancellation_email", ".html"),
        ("counter_threshold_reached_email", ".html"),
        ("feedback_email", ".html"),
        ("generic_email", ".html"),
        ("missed_reservation_email", ".html"),
        ("facility_rules_tutorial_email", ".html"),
        ("new_task_email", ".html"),
        ("out_of_time_reservation_email", ".html"),
        ("reorder_supplies_reminder_email", ".html"),
        ("reservation_ending_reminder_email", ".html"),
        ("reservation_reminder_email", ".html"),
        ("reservation_warning_email", ".html"),
        ("safety_issue_email", ".html"),
        ("scheduled_outage_reminder_email", ".html"),
        ("staff_charge_reminder_email", ".html"),
        ("task_status_notification", ".html"),
        ("tool_qualification_expiration_email", ".html"),
        ("training_invitation_declined_email", ".html"),
        ("training_invitation_received_email", ".html"),
        ("training_request_submitted_email", ".html"),
        ("training_session_cancelled_email", ".html"),
        ("grant_access_email", ".html"),
        ("unauthorized_tool_access_email", ".html"),
        ("usage_reminder_email", ".html"),
        ("user_access_expiration_reminder_email", ".html"),
        ("reservation_created_user_email", ".html"),
        ("reservation_cancelled_user_email", ".html"),
        ("weekend_access_email", ".html"),
        ("recurring_charges_reminder_email", ".html"),
        ("shadowing_verification_notification_email", ".html"),
        ("wait_list_notification_email", ".html"),
        ("tool_required_unanswered_questions_email", ".html"),
    ]


@customization(key="rates", title="Rates")
class RatesCustomization(CustomizationBase):
    variables = {"rates_expand_table": ""}
    files = [("rates", ".json")]

    def save(self, request, element=None):
        errors = super().save(request, element)
        if not errors:
            from NEMO.rates import rate_class

            rate_class.load_rates(force_reload=True)
        return errors


def get_media_file_contents(file_name):
    """Get the contents of a media file if it exists. Return a blank string if it does not exist."""
    if not default_storage.exists(file_name):
        return ""
    with default_storage.open(file_name) as opened_file:
        read_file = opened_file.read()
        try:
            return read_file.decode().strip()
        except UnicodeDecodeError:
            return read_file


def store_media_file(content, file_name):
    """
    Delete any existing media file with the same name and save the new content into file_name in the media directory.
    If the content is blank then no new file is created.
    """
    default_storage.delete(file_name)
    if content:
        default_storage.save(file_name, content)


# This method should not be used anymore. Instead, use XCustomization.get(name)
def get_customization(name, raise_exception=True):
    customizable_key_values = CustomizationBase._all_variables()
    if name not in customizable_key_values.keys():
        raise InvalidCustomizationException(name)
    default_value = customizable_key_values[name]
    try:
        return Customization.objects.get(name=name).value
    except Customization.DoesNotExist:
        # return default value
        return default_value
    except Exception:
        if raise_exception:
            raise
        else:
            return default_value


# This method should not be used anymore. Instead, use XCustomization.set(name, value)
def set_customization(name, value):
    customizable_key_values = CustomizationBase._all_variables()
    if name not in customizable_key_values:
        raise InvalidCustomizationException(name, value)
    if value:
        Customization.objects.update_or_create(name=name, defaults={"value": value})
    else:
        try:
            Customization.objects.get(name=name).delete()
        except Customization.DoesNotExist:
            pass


@administrator_required
@require_GET
def customization(request, key: str = "application"):
    customization_instance: CustomizationBase = CustomizationBase.get_instance(key)
    if not customization_instance:
        return HttpResponseNotFound(f"Customizations with key: '{key}' not found")
    return render(request, "customizations/customizations.html", customization_instance.context())


@administrator_required
@require_POST
def customize(request, key, element=None):
    customization_instance: CustomizationBase = CustomizationBase.get_instance(key)
    if not customization_instance:
        return HttpResponseNotFound(f"Customizations with key: '{key}' not found")
    errors = customization_instance.save(request, element)
    if errors:
        messages.error(request, f"Please correct the errors below:")
        return render(
            request, "customizations/customizations.html", {"errors": errors, **customization_instance.context()}
        )
    else:
        messages.success(request, f"{customization_instance.title} settings saved successfully")
        return redirect("customization", key)
