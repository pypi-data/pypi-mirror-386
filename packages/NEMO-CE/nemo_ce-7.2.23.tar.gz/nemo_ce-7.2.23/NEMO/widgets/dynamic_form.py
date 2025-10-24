from __future__ import annotations

import random
import re
import sys
from collections import Counter
from copy import copy
from json import dumps, loads
from logging import getLogger
from typing import Any, Callable, Dict, List, Optional, Type, Union

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.http import HttpResponse, QueryDict
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET, require_POST

from NEMO.evaluators import evaluate_expression, get_expression_variables
from NEMO.exceptions import RequiredUnansweredQuestionsException
from NEMO.models import Consumable, Task, ToolUsageCounter, UsageEvent
from NEMO.utilities import EmptyHttpRequest, quiet_int, slugify_underscore, strtobool
from NEMO.views.consumables import make_withdrawal

dynamic_form_logger = getLogger(__name__)


GROUP_TYPE_FIELD_KEY = "group"


class PostUsageQuestion:
    question_type = "Question"

    required_span = '<span class="required-question-star">*</span>'

    def __init__(self, properties: Dict, index: int = None, initial_data=None):
        self.properties = properties
        self.name = self._init_property("name")
        self.initial_name = self.name
        self.title = self._init_property("title")
        self.title_html = self._init_property("title_html")
        self.help = self._init_property("help")
        self.type = self._init_property("type")
        self.max_width = self._init_property("max-width")
        self.maxlength = self._init_property("maxlength")
        self.placeholder = self._init_property("placeholder")
        self.prefix = self._init_property("prefix")
        self.suffix = self._init_property("suffix")
        self.pattern = self._init_property("pattern")
        self.min = self._init_property("min")
        self.max = self._init_property("max")
        self.precision = self._init_property("precision")
        self.step = self._init_property("step")
        self.rows = self._init_property("rows")
        self.auto_resize = self._init_property("auto_resize", boolean=True)
        self.consumable = self._init_property("consumable")
        self.consumable_id = self._init_property("consumable_id")
        self.required = self._init_property("required", boolean=True)
        self.inline = self._init_property("inline", boolean=True)
        self.readonly = self._init_property("readonly", boolean=True)
        self.show_formula_preview = self._init_property("show_formula_preview", boolean=True)
        # For backwards compatibility keep default choice
        self.default_value = (
            self._init_property("default_value")
            if self._init_property("default_value") is not None
            else self._init_property("default_choice")
        )
        self.choices = self._init_property("choices")
        self.labels = self._init_property("labels")
        self.formula = self._init_property("formula")
        self.options = self._init_property("options")
        self.form_row = self._init_property("form_row")
        self.row_cell = self._init_property("row_cell")
        self.group_add_button_name = self._init_property("group_add_button_name") or "Add"
        self.index = index
        if index and not isinstance(self, PostUsageGroupQuestion):
            self.name = f"{self.name}_{index}"
        # form_name is used in forms and extraction to avoid potential conflicts with other data
        self.form_name = f"df_{slugify_underscore(self.name)}"
        self.all_questions: List[PostUsageQuestion] = []
        self.is_sub_question: bool = False
        self.initial_data = initial_data

    def get_default_value(self):
        # Initial data always has precedence over the default value from the question definition
        return self.initial_data if self.initial_data is not None else self.default_value

    def _init_property(self, prop: str, boolean: bool = False) -> Any:
        if boolean:
            return True if prop in self.properties and self.properties[prop] is True else False
        else:
            return self.properties[prop] if prop in self.properties else None

    @property
    def has_consumable(self):
        return self.consumable_id or self.consumable

    def get_consumable(self) -> Consumable:
        return (
            Consumable.objects.get(pk=self.consumable_id)
            if self.consumable_id
            else Consumable.objects.get(name=self.consumable)
        )

    def validate(self):
        self.validate_property_exists("name")
        self.validate_property_exists("title")
        self.validate_property_exists("type")

    def render(self, virtual_inputs: bool, item, dynamic_field_name, extra_class="") -> str:
        return self.render_element(virtual_inputs, item, dynamic_field_name, extra_class) + self.render_script(
            virtual_inputs, item, dynamic_field_name
        )

    def render_as_text(self) -> str:
        result = f"{self.title}\n"
        result += "<strong>your answer</strong>"
        if self.choices:
            result += " (possible choices: " + "|".join(self.choices) + ")"
        return result

    def render_element(self, virtual_inputs: bool, item, dynamic_field_name: str, extra_class="") -> str:
        return ""

    def render_script(self, virtual_inputs: bool, item, dynamic_field_name: str) -> str:
        return ""

    def extract(self, request, index=None) -> Dict:
        answered_question = copy(self.properties)
        user_input = request.POST.get(f"{self.form_name}_{index}" if index else self.form_name)
        if user_input:
            answered_question["user_input"] = user_input
        return answered_question

    def extract_for_formula(self, request, index=None) -> Any:
        extracted = self.extract(request, index)
        return extracted["user_input"] if "user_input" in extracted else None

    def validate_property_exists(self, prop: str):
        try:
            self.properties[prop]
        except KeyError:
            raise Exception(f"{self.question_type} requires property '{prop}' to be defined")

    def validate_labels_and_choices(self):
        self.validate_property_exists("choices")
        if "labels" in self.properties:
            labels = self.properties["labels"]
            if not isinstance(labels, dict):
                label_length = len(labels)
            else:
                label_length = 0
                for element, value in labels.items():
                    if isinstance(value, list):  # Recursively check if the element is a sublist
                        label_length += len(value)
                    else:
                        label_length += 1
            if label_length != len(self.properties["choices"]):
                raise Exception("When using labels you need one for each choice")

    @staticmethod
    def load_questions(questions: Optional[List[Dict]], index: int = None, initial_data: Union[Dict, str] = None):
        user_inputs = get_submitted_user_inputs(initial_data)
        questions_to_load = questions or []
        post_usage_questions: List[PostUsageQuestion] = []
        for question in questions_to_load:
            question_initial_data = user_inputs[question["name"]] if question["name"] in user_inputs else None
            post_usage_questions.append(
                question_types.get(question["type"], PostUsageQuestion)(question, index, question_initial_data)
            )
        return post_usage_questions


class PostUsageRadioQuestion(PostUsageQuestion):
    question_type = "Question of type radio"

    def validate(self):
        super().validate()
        self.validate_labels_and_choices()

    def render_element(self, virtual_inputs: bool, item, dynamic_field_name: str, extra_class="") -> str:
        title = self.title_html or self.title
        max_width = f"max-width:{self.max_width}px" if self.max_width else ""
        result = f'<div class="form-group {extra_class}" style="{max_width}">'
        result += f'<label for="{self.form_name}" style="white-space: pre-wrap">{title}{self.required_span if self.required else ""}</label>'
        result += f"<div class='{'form-control-static' if self.inline else ''}'>"
        for index, choice in enumerate(self.choices):
            label = self.labels[index] if self.labels else choice
            result += f'<div class="radio{"-inline" if self.inline else ""}">'
            required = "required" if self.required else ""
            is_default_choice = (
                "checked" if self.get_default_value() is not None and self.get_default_value() == choice else ""
            )
            result += f'<label><input type="radio" name="{self.form_name}" value="{choice}" {required} {is_default_choice}>{label}</label>'
            result += "</div>"
        result += "</div>"
        result += "</div>"
        return result


class PostUsageCheckboxQuestion(PostUsageQuestion):
    question_type = "Question of type checkbox"

    def validate(self):
        super().validate()
        self.validate_labels_and_choices()

    def render_element(self, virtual_inputs: bool, item, dynamic_field_name: str, extra_class="") -> str:
        title = self.title_html or self.title
        max_width = f"max-width:{self.max_width}px" if self.max_width else ""
        result = f'<div class="form-group {extra_class}" style="{max_width}>'
        result += f'<label for="{self.form_name}" style="white-space: pre-wrap">{title}{self.required_span if self.required else ""}</label>'
        result += f'<input aria-label="hidden field used for required answer" id="required_{ self.form_name }" type="checkbox" value="" style="opacity: 0;height: 1px;width: 1px;" { "required" if self.required else "" } {"checked" if self.get_default_value() else ""}/>'
        result += f"<div class='{'form-control-static' if self.inline else ''}'>"
        for index, choice in enumerate(self.choices):
            label = self.labels[index] if self.labels else choice
            result += f'<div class="checkbox{"-inline" if self.inline else ""}">'
            required = f"""onclick="checkbox_required('{self.form_name}')" """ if self.required else ""
            is_default_choice = (
                "checked"
                if self.get_default_value() is not None
                and (
                    self.get_default_value() == choice
                    or isinstance(self.get_default_value(), List)
                    and choice in self.get_default_value()
                )
                else ""
            )
            result += f'<label><input type="checkbox" name="{self.form_name}" value="{choice}" {required} {is_default_choice}>{label}</label>'
            result += "</div>"
        result += "</div>"
        result += "</div>"
        return result

    def render_script(self, virtual_inputs: bool, item, dynamic_field_name: str) -> str:
        result = "<script>"
        result += "function checkbox_required(form_name) {"
        result += "if ($('input[name=' + form_name + ']:checkbox:checked').length > 0) {"
        result += "$('#required_' + form_name).prop('checked', true).change();"
        result += "} else {"
        result += "$('#required_'+ form_name).prop('checked', false).change();"
        result += "} }"
        result += "</script>"
        return result

    def extract(self, request, index=None) -> Dict:
        answered_question = copy(self.properties)
        user_input = request.POST.getlist(f"{self.form_name}_{index}" if index else self.form_name)
        if user_input:
            answered_question["user_input"] = user_input
        return answered_question


class PostUsageDropdownQuestion(PostUsageQuestion):
    question_type = "Question of type dropdown"

    def validate(self):
        super().validate()
        self.validate_labels_and_choices()

    def render_element(self, virtual_inputs: bool, item, dynamic_field_name: str, extra_class="") -> str:
        title = self.title_html or self.title
        max_width = f"max-width:{self.max_width}px" if self.max_width else ""
        result = f'<div class="form-group {extra_class}" style="{max_width}">'
        result += f'<label for="{self.form_name}" style="white-space: pre-wrap">{title}{self.required_span if self.required else ""}</label>'
        required = "required" if self.required else ""
        result += f'<select name="{self.form_name}" {required} class="form-control">'
        blank_disabled = 'disabled="disabled"' if required else ""
        placeholder = self.placeholder if self.placeholder else "Select an option"
        result += f'<option {blank_disabled} selected="selected" value="">{placeholder}</option>'
        index = 0
        for key in self.labels or self.choices:
            if not self.labels:
                label = self.choices[index]
            elif isinstance(self.labels, dict):
                label = self.labels[key]
            else:
                label = self.labels[index]
            if isinstance(label, list):
                result += f'<optgroup label="{key}">\n'
                for item in label:
                    choice = self.choices[index]
                    result += self._render_choice_option(choice, item)
                    index += 1
                result += "</optgroup>\n"
            else:
                choice = self.choices[index]
                result += self._render_choice_option(choice, label)
                index += 1
        result += "</select>"
        if self.help:
            result += f'<div style="font-size:smaller;color:#999;">{self.help}</div>'
        result += "</div>"
        return result

    def _render_choice_option(self, choice, label) -> str:
        is_default_choice = (
            "selected" if self.get_default_value() is not None and self.get_default_value() == choice else ""
        )
        return f'<option value="{choice}" {is_default_choice}>{label}</option>'


class PostUsageTextFieldQuestion(PostUsageQuestion):
    question_type = "Question of type text"

    def render_element(self, virtual_inputs: bool, item, dynamic_field_name: str, extra_class="") -> str:
        title = self.title_html or self.title
        max_width = f"max-width:{self.max_width}px" if self.max_width else ""
        result = f'<div class="form-group {extra_class}" style="{max_width}">'
        result += f'<label for="{self.form_name}" style="white-space: pre-wrap">{title}{self.required_span if self.required else ""}</label>'
        input_group_required = True if self.prefix or self.suffix else False
        if input_group_required:
            result += '<div class="input-group">'
        if self.prefix:
            result += f'<span class="input-group-addon">{self.prefix}</span>'
        readonly = "readonly" if self.readonly else ""
        required = "required" if self.required and not self.readonly else ""
        pattern = f'pattern="{self.pattern}"' if self.pattern else ""
        placeholder = f'placeholder="{self.placeholder}"' if self.placeholder else ""
        default_value = f'value="{self.get_default_value()}"' if self.get_default_value() is not None else ""
        result += self.render_input(readonly, required, pattern, placeholder, default_value)
        if self.suffix:
            result += f'<span class="input-group-addon">{self.suffix}</span>'
        if input_group_required:
            result += "</div>"
        if self.help:
            result += f'<div style="font-size:smaller;color:#999;">{self.help}</div>'
        result += "</div>"
        return result

    def render_input(self, readonly: str, required: str, pattern: str, placeholder: str, default_value: str) -> str:
        maxlength = f'maxlength="{self.maxlength}"' if self.maxlength else ""
        return f'<input type="text" class="form-control" id="{self.form_name}" name="{self.form_name}" {maxlength} {placeholder} {pattern} {default_value} {required} {readonly} spellcheck="false" autocapitalize="off" autocomplete="off" autocorrect="off">'

    def render_script(self, virtual_inputs: bool, item, dynamic_field_name: str) -> str:
        if virtual_inputs:
            return f"<script>$('#{self.form_name}').keyboard();</script>"
        return super().render_script(virtual_inputs, item, dynamic_field_name)

    def render_as_text(self) -> str:
        result = f"{self.title}\n"
        if self.prefix:
            result += self.prefix
        result += "<strong>your answer</strong>"
        if self.suffix:
            result += f" {self.suffix}"
        return result


class PostUsageTextAreaFieldQuestion(PostUsageTextFieldQuestion):
    question_type = "Question of type textarea"

    def render_input(self, readonly: str, required: str, pattern: str, placeholder: str, default_value: str) -> str:
        rows = f'rows="{str(self.rows)}"' if self.rows else ""
        rows_parameter = f", {str(self.rows)}" if self.rows else ""
        on_input = f'oninput="auto_size_textarea(this{rows_parameter});"' if self.auto_resize else ""
        return f'<textarea {on_input} class="form-control" id="{self.form_name}" name="{self.form_name}" {rows} {placeholder} {required} {readonly} style="height:inherit" spellcheck="false" autocapitalize="off" autocomplete="off" autocorrect="off">{self.get_default_value() or ""}</textarea>'

    def render_script(self, virtual_inputs: bool, item, dynamic_field_name: str) -> str:
        super_script = super().render_script(virtual_inputs, item, dynamic_field_name)
        if self.auto_resize:
            script_only = super_script.replace("<script>", "").replace("</script>", "")
            rows_parameter = f", {str(self.rows)}" if self.rows else ""
            return f"<script>{script_only};auto_size_textarea($('#{self.form_name}')[0]{rows_parameter})</script>"
        return super_script


class PostUsageNumberFieldQuestion(PostUsageTextFieldQuestion):
    question_type = "Question of type number"

    def render_input(self, readonly: str, required: str, pattern: str, placeholder: str, default_value: str) -> str:
        minimum = f'min="{self.min}"' if self.min else ""
        maximum = f'max="{self.max}"' if self.max else ""
        step = f'step="{self.step}"' if self.step else ""
        return f'<input type="number" class="form-control" id="{self.form_name}" name="{self.form_name}" {placeholder} {pattern} {minimum} {maximum} {default_value} {step} {required} {readonly} spellcheck="false" autocapitalize="off" autocomplete="off" autocorrect="off">'

    def render_script(self, virtual_inputs: bool, item, dynamic_field_name: str) -> str:
        if virtual_inputs:
            return f"<script>$('#{self.form_name}').numpad({{'readonly': false, 'hidePlusMinusButton': true, 'hideDecimalButton': true}});</script>"
        return super().render_script(virtual_inputs, item, dynamic_field_name)

    def render_as_text(self) -> str:
        result = super().render_as_text()
        if self.min or self.max:
            result += " ("
            if self.min:
                result += f"min: {self.min}"
            if self.max:
                if self.min:
                    result += ", "
                result += f"max: {self.min}"
            result += ")"
        return result

    def extract_for_formula(self, request, index=None) -> Any:
        value = super().extract_for_formula(request, index)
        return int(value) if value is not None else None


class PostUsageFloatFieldQuestion(PostUsageTextFieldQuestion):
    question_type = "Question of type float"

    def render_input(self, readonly: str, required: str, pattern: str, placeholder: str, default_value: str) -> str:
        precision = self.precision if self.precision else 2
        pattern = f'pattern="^\s*(?=.*[0-9])\d*(?:\.\d{"{1," + str(precision) + "}"})?\s*$"'
        return f'<input type="text" class="form-control" id="{self.form_name}" name="{self.form_name}" {placeholder} {pattern} {default_value} {required} {readonly} spellcheck="false" autocapitalize="off" autocomplete="off" autocorrect="off">'

    def render_script(self, virtual_inputs: bool, item, dynamic_field_name: str) -> str:
        if virtual_inputs:
            return f"<script>$('#{self.form_name}').numpad({{'readonly': false, 'hidePlusMinusButton': true, 'hideDecimalButton': false}});</script>"
        return super().render_script(virtual_inputs, item, dynamic_field_name)

    def extract_for_formula(self, request, index=None) -> Any:
        value = super().extract_for_formula(request, index)
        return float(value) if value is not None else None


class PostUsageFormulaQuestion(PostUsageQuestion):
    question_type = "Question of type formula"

    @property
    def all_questions_by_name(self):
        return {question.name: question for question in self.all_questions}

    @property
    def all_questions_by_form_name(self):
        return {question.form_name: question for question in self.all_questions}

    def render_element(self, virtual_inputs: bool, item, dynamic_field_name: str, extra_class="") -> str:
        result = f'<input type="hidden" id="{self.form_name}" name="{self.form_name}">'
        if self.show_formula_preview:
            title = self.title_html or self.title
            max_width = f"max-width:{self.max_width}px" if self.max_width else ""
            formula_url = f'data-formula-url="{reverse("formula_preview", args=[ContentType.objects.get_for_model(item).id, item.id, dynamic_field_name, self.name])}"'
            result += f'<div class="form-group {extra_class}" style="{max_width}">'
            result += f'<label for="{self.form_name}" style="white-space: pre-wrap">{title}</label>'
            result += f'<input type="text" {formula_url} disabled class="form-control formula-input-preview" value="{self.get_default_value() if self.get_default_value() is not None else ""}">'
            result += "</div>"
        return result

    def validate(self):
        super().validate()
        self.validate_property_exists("formula")
        # Now validate variables
        formula_variables = get_expression_variables(self.formula)
        valid_question_names = {
            q.form_name: q.name
            for q in self.all_questions
            if not isinstance(q, PostUsageGroupQuestion) and not q == self
        }
        diff = formula_variables.difference(set(valid_question_names.values()).union(valid_question_names.keys()))
        if diff:
            if len(diff) == 1:
                raise Exception(
                    f"formula variable {next(iter(diff))} is not a valid question name, valid choices are: {', '.join(valid_question_names.values())}"
                )
            else:
                raise Exception(
                    f"formula variables {list(diff)} are not valid question names, valid choices are: {', '.join(valid_question_names.values())}"
                )
        if self.has_consumable:
            # The result of the formula must be an int, so let's add some random variables and check
            formula_and_values = {}
            for var in formula_variables:
                form_name = var
                if var in valid_question_names.values():
                    form_name = [key for key, val in valid_question_names.items() if val == var][0]
                if isinstance(self.all_questions_by_name[var], PostUsageNumberFieldQuestion):
                    formula_and_values[form_name] = str(random.randint(1, 100))
                elif isinstance(self.all_questions_by_name[var], PostUsageFloatFieldQuestion):
                    formula_and_values[form_name] = str(random.uniform(1.0, 100.0))
            http_request = EmptyHttpRequest()
            http_request.POST = QueryDict(mutable=True)
            http_request.POST.update(formula_and_values)
            int(self.extract_for_formula(http_request))

    def extract(self, request, index=None) -> Dict:
        answered_question = copy(self.properties)
        value = self.extract_for_formula(request, index)
        if value is not None:
            answered_question["user_input"] = str(value)
        return answered_question

    def extract_for_formula(self, request, index=None) -> Any:
        formula_variables = get_expression_variables(self.formula)
        # we need to substitute variables with their real form name
        # i.e. name="test Variable" becomes "df_test_variable" in the form
        formula = self.formula
        form_name_variables = {}
        for variable in formula_variables:
            # we still want to allow using directly "df_test_variable" in formula
            if variable in self.all_questions_by_form_name:
                question_form_name = variable
            else:
                question_form_name = self.all_questions_by_name[variable].form_name
            form_key_variable = question_form_name if index is None else f"{question_form_name}_{index}"
            form_name_variables[question_form_name] = form_key_variable
            formula = re.sub(r"\b" + re.escape(variable) + r"\b", form_key_variable, formula)
        # extract values from questions and use them in formula
        extracted_form_values = {}
        for form_name, form_key in form_name_variables.items():
            matching_question = self.all_questions_by_form_name[form_name]
            # For formulas outside of groups using a group question,
            # the variable should contain the list of values from the groups
            formula_outside_group_using_group = not self.is_sub_question and matching_question.is_sub_question
            if formula_outside_group_using_group:
                pattern = match_group_index(form_key)
                # let's grab indexes just like we do for group questions
                indexes = [
                    quiet_int(pattern.match(key).group(2), None) for key in request.POST.keys() if pattern.match(key)
                ]
                # now extract all the values from the group into a list
                value = [
                    matching_question.extract_for_formula(request, index)
                    for index in indexes
                    if matching_question.extract_for_formula(request, index) is not None
                ]
            else:
                # Special case if we are using a variable/question outside a group while we are in the group
                formula_inside_group_not_using_group = self.is_sub_question and not matching_question.is_sub_question
                value = matching_question.extract_for_formula(
                    request, index if not formula_inside_group_not_using_group else None
                )
            extracted_form_values[form_key] = value
        # Allow everything other than None as valid value. If None is present
        # we skip the whole formula evaluation
        all_valid = all([val is not None for val in extracted_form_values.values()])
        return evaluate_expression(formula, **extracted_form_values) if all_valid else None


class PostUsageRadioReportProblemQuestion(PostUsageRadioQuestion):
    question_type = "Question of type radio report problem"

    def __init__(self, properties: Dict, index: int = None, initial_data=None):
        properties["choices"] = ["true", "false"]
        if not properties.get("labels"):
            properties["labels"] = ["Yes", "No"]
        super().__init__(properties, index, initial_data)

    def validate(self):
        super().validate()
        self.validate_property_exists("options")
        task = Task(**self.options)
        try:
            if not task.problem_description:
                raise ValidationError({"problem_description": _("This field is required")})
            task.full_clean(exclude=["tool", "creator", "urgency", "safety_hazard", "force_shutdown"])
        except ValidationError as e:
            raise Exception(f"{self.question_type} options are invalid: {e.message_dict}")


class PostUsageGroupQuestion(PostUsageQuestion):
    question_type = "Question of type group"

    def __init__(self, properties: Dict, index: int = None, initial_data=None):
        super().__init__(properties, index, initial_data)
        self.max_number = self._init_property("max_number")
        # we need a safe group name to use in js function and variable names
        self.group_name = slugify_underscore(self.name)
        self.load_sub_questions(index)
        for sub_question in self.sub_questions:
            sub_question.is_sub_question = True

    def load_sub_questions(self, index, initial_data=None):
        self.sub_questions = PostUsageQuestion.load_questions(self._init_property("questions"), index)
        if initial_data:
            for sub_question in self.sub_questions:
                sub_question.initial_data = initial_data.get(sub_question.initial_name, None)

    def validate(self):
        super().validate()
        self.validate_property_exists("questions")
        self.validate_property_exists("max_number")
        for sub_question in self.sub_questions:
            if isinstance(sub_question, PostUsageRadioReportProblemQuestion):
                raise Exception(f"{sub_question.question_type} cannot be used inside a group question")
            sub_question.validate()

    def render_element(self, virtual_inputs: bool, item, dynamic_field_name: str, extra_class="") -> str:
        title = self.title_html or self.title
        result = f'<div class="{extra_class}">'
        result += f'<div class="form-group"><div style="white-space: pre-wrap">{title}</div></div>'
        result += f'<div class="{self.group_name}_container">'
        # It's a bit more complicated here, we need to render multiple groups if we have initial data
        # So we change the index, reload sub questions and render each of them
        if self.initial_data:
            for index, data in enumerate(self.initial_data):
                self.load_sub_questions(index, data)
                result += self.render_group_question(virtual_inputs, item, dynamic_field_name)
                result += "</div>"
        else:
            result += self.render_group_question(virtual_inputs, item, dynamic_field_name)
            result += "</div>"
        result += "</div>"
        result += '<div class="form-group">'
        add_group_url = (
            reverse(
                "render_group_question",
                args=[ContentType.objects.get_for_model(item).id, item.id, dynamic_field_name, self.group_name],
            )
            + f"?virtual_inputs={virtual_inputs}"
        )
        result += f'<button class="{self.group_name}_add_button" type="button" onclick="add_group_question(this, \'{self.group_name}\', {self.max_number}, \'{add_group_url}\')">{self.group_add_button_name}</button>'
        result += "</div>"
        result += "</div>"
        return result

    def render_group_question(self, virtual_inputs: bool, item, field_name: str) -> str:
        result = ""
        result += f'<div class="{self.group_name}_question" data-group-index="{self.index or 0}" style="padding-top: 10px; padding-bottom: 10px; border-top: 1px solid lightgray">'
        result += render_grid_questions(self.sub_questions, item, field_name, virtual_inputs)
        if self.index:
            result += f'<button type="button" onclick="remove_group_question(this, \'{self.group_name}\', {self.max_number});">Remove</button>'
        return result

    def render_as_text(self) -> str:
        result = f"{self.title}\n"
        for question in self.sub_questions:
            result += question.render_as_text()
        return result

    def extract(self, request, index=None) -> Dict:
        # For group question, we also have to look for answers submitted
        # with a numbered suffix (i.e. question, question_1, question_2 etc.)
        # The result of the extraction will be a dictionary, with the keys being the group number,
        # and the values the user inputs for all questions of the group.
        sub_results = copy(self.properties)
        inputs = {}
        for key in request.POST.keys():
            for sub_question in self.sub_questions:
                match = match_group_index(sub_question.form_name).match(key)
                if match:
                    index = quiet_int(match.group(2), None)  # extract index
                    index_string = str(index or 0)
                    inputs.setdefault(index_string, {})
                    inputs[index_string][sub_question.name] = sub_question.extract(request, index).get("user_input")
        sub_results["user_input"] = inputs
        return sub_results


class DynamicForm:
    def __init__(self, questions, initial_data=None):
        self.untreated_questions = []
        self.questions = []
        if questions:
            self.untreated_questions = loads(questions)
            self.questions: List[PostUsageQuestion] = PostUsageQuestion.load_questions(
                self.untreated_questions, initial_data=initial_data
            )
        # Add all the questions to each question, for extra processing if needed (in Formula for example)
        subs = [sub_q for q in self.questions if isinstance(q, PostUsageGroupQuestion) for sub_q in q.sub_questions]
        all_questions = self.questions + subs
        for initialized_question in self.questions:
            initialized_question.all_questions = all_questions
            if isinstance(initialized_question, PostUsageGroupQuestion):
                for sub_question in initialized_question.sub_questions:
                    sub_question.all_questions = all_questions

    def render(self, item, dynamic_field_name: str, virtual_inputs: bool = False):
        result = ""
        item_type_id = ContentType.objects.get_for_model(item).id
        if self.questions:
            data_selector = f'.dynamic_form[data-item-type-id="{item_type_id}"][data-item-id="{item.id}"][data-field-name="{dynamic_field_name}"]'
            result += f"""
            <script>
            if (!$) {{ $ = django.jQuery; }}
            
            $('body').on('change keyup', '{data_selector} input, {data_selector} select, {data_selector} textarea', function(event)
            {{
                let event_data = {get_js_event_data(item, dynamic_field_name)}
                event_data["input_field_name"] = $(event.target).attr("name");
                $('body').trigger('dynamic-form-field-changed', [event_data]);
            }});

            function remove_group_question(element, group_name, max_number)
            {{
                let element_jq = $(element);
                let dynamic_form_element = element_jq.closest('.dynamic_form');
                element_jq.parents("." + group_name +"_question").remove();
                let event_data = {get_js_event_data(item, dynamic_field_name, {"add": False, "remove": True})}
                event_data["group_name"] = group_name;
                event_data["max_number"] = max_number;
                $("body").trigger("dynamic-form-group-changed", [event_data]);
            }}
            
            function add_group_question(element, group_name, max_number, render_group_url)
            {{
                let element_jq = $(element);
                let dynamic_form_element = element_jq.closest('.dynamic_form');
                let highest_group_index = Math.max(...dynamic_form_element.find("." + group_name + "_question").map(function() {{return isNaN($(this).data("group-index")) ? 0 : +$(this).data("group-index");}}).get());
                $.ajax({{ type: "GET", url: render_group_url + "&index=" + (highest_group_index + 1), success : function(response)
                {{
                    dynamic_form_element.find("." + group_name + "_container").append(response);
                    let event_data = {get_js_event_data(item, dynamic_field_name, {"add": True, "remove": False})}
                    event_data["group_name"] = group_name;
                    event_data["max_number"] = max_number;
                    $("body").trigger("dynamic-form-group-changed", [event_data]);
                }}
                }});
            }}
            
            $("body").on("dynamic-form-group-changed", function(event, event_data)
            {{
                // Updated add button visibility
                let group_name = event_data.group_name;
                let dynamic_form_element = $('.dynamic_form[data-item-type-id="' + event_data.item_type_id + '"][data-item-id="' + event_data.item_id + '"][data-field-name="' + event_data.field_name + '"]');
                let current_question_count = dynamic_form_element.find("." + group_name + "_question").length;
                if (current_question_count < event_data.max_number)
                {{
                    dynamic_form_element.find("." + group_name + "_add_button").show();
                }}
                else
                {{
                    dynamic_form_element.find("." + group_name + "_add_button").hide();
                }}
            }});
            
            $("body").on("dynamic-form-field-changed", function(event, event_data)
            {{
                let dynamic_form_element = $('.dynamic_form[data-item-type-id="' + event_data.item_type_id + '"][data-item-id="' + event_data.item_id + '"][data-field-name="' + event_data.field_name + '"]');
                dynamic_form_element.find(".formula-input-preview").each(function()
                {{
                    let element_jq = $(this);
                    let data = element_jq.attr("form") ? $('#'+element_jq.attr("form")).serialize() : element_jq.closest('form').serialize();
                    if (typeof csrf_token === 'function')
                    {{
                        data += "&csrfmiddlewaretoken=" + csrf_token();
                    }}
                    $.ajax({{ type: "POST", data: data, url: element_jq.data("formula-url"), success : function(response)
                    {{
                        element_jq.val(response);
                    }}
                    }});
                }});
            }});
            
            </script>"""
        result += f'<div class="dynamic_form" data-item-type-id="{item_type_id}" data-item-id="{item.id}" data-field-name="{dynamic_field_name}">{render_grid_questions(self.questions, item, dynamic_field_name, virtual_inputs)}</div>'
        return mark_safe(result)

    def validate(self, item, dynamic_field_name: str):
        # We need to validate the raw json for types
        for question in self.untreated_questions:
            if question["type"] not in question_types.keys():
                raise Exception(f"type has to be one of {', '.join(question_types.keys())}, not {question['type']}")
            if question["type"] == GROUP_TYPE_FIELD_KEY and "questions" in question:
                for sub_question in question["questions"]:
                    if sub_question["type"] not in question_types.keys():
                        raise Exception(
                            f"type has to be one of {', '.join(question_types.keys())}, not {sub_question['type']}"
                        )
        for question in self.questions:
            question.validate()
        # Test the rendering
        self.render(item, dynamic_field_name)
        # Check for duplicate names, and that if consumable exists they are linked to a number question
        names = []
        for question in self.questions:
            names.append(question.name)
            validate_consumable_for_question(question)
            if isinstance(question, PostUsageGroupQuestion):
                for sub_question in question.sub_questions:
                    names.append(sub_question.name)
                    validate_consumable_for_question(sub_question)
        duplicate_names = [k for k, v in Counter(names).items() if v > 1]
        if duplicate_names:
            raise Exception(f"Question names need to be unique. Duplicates were found: {duplicate_names}")

    def extract(self, request) -> str:
        results = {}
        required_unanswered_questions = []
        for question in self.questions:
            results[question.name] = question.extract(request)
            required_unanswered_questions.extend(self._check_for_required_unanswered_questions(results, question))
        run_data = dumps(results, indent="\t") if len(results) else ""
        if required_unanswered_questions:
            raise RequiredUnansweredQuestionsException(run_data, required_unanswered_questions)
        return run_data

    def _check_for_required_unanswered_questions(
        self, results: Dict, question: PostUsageQuestion
    ) -> Optional[List[PostUsageQuestion]]:
        # This method will check for required unanswered questions and if some are found, will fill them with blank and return them
        required_unanswered_questions = []
        user_input = results[question.name].get("user_input")
        user_input = user_input.strip() if user_input and isinstance(user_input, str) else user_input
        if not isinstance(question, PostUsageGroupQuestion) and question.required and not user_input:
            results[question.name]["user_input"] = ""
            required_unanswered_questions.append(question)
        elif isinstance(question, PostUsageGroupQuestion):
            blank_user_input = {"0": {}}
            for sub_question in question.sub_questions:
                if sub_question.required and (not user_input or not user_input.get("0", {}).get(sub_question.name)):
                    blank_user_input["0"][sub_question.name] = ""
                    required_unanswered_questions.append(sub_question)
            if required_unanswered_questions:
                results[question.name]["user_input"] = blank_user_input
        return required_unanswered_questions

    def filter_questions(self, function: Callable[[PostUsageQuestion], bool]) -> List[PostUsageQuestion]:
        results = []
        for question in self.questions:
            if function(question):
                results.append(question)
            elif isinstance(question, PostUsageGroupQuestion):
                for sub_question in question.sub_questions:
                    if function(sub_question):
                        results.append(sub_question)
        return results

    def process_run_data(self, usage_event: UsageEvent, run_data: str, request=None):
        try:
            run_data_json = loads(run_data)
        except Exception as error:
            dynamic_form_logger.debug(error)
            return
        self._charge_for_consumables(usage_event, run_data_json, request)
        self._update_tool_counters(usage_event, run_data_json)
        self._report_problems(usage_event, run_data_json, request)

    def _charge_for_consumables(self, usage_event, run_data_json: Dict, request=None):
        customer = usage_event.user
        merchant = usage_event.operator
        project = usage_event.project
        for question in self.questions:
            input_data = run_data_json[question.name] if question.name in run_data_json else None
            withdraw_consumable_for_question(question, input_data, customer, merchant, project, usage_event, request)
            if isinstance(question, PostUsageGroupQuestion):
                for sub_question in question.sub_questions:
                    withdraw_consumable_for_question(
                        sub_question, input_data, customer, merchant, project, usage_event, request
                    )

    def _update_tool_counters(self, usage_event: UsageEvent, run_data_json: Dict):
        # This function increments/decrements all counters associated with the given tool
        pre_post = "post"
        if run_data_json:
            if usage_event.pre_run_data and usage_event.run_data:
                # if we have both check which one matches
                if loads(usage_event.pre_run_data) == run_data_json:
                    pre_post = "pre"
            elif usage_event.pre_run_data:
                # if we only have pre_run_data then it has to be pre usage question
                pre_post = "pre"
        counter_question_name = f"tool_{pre_post}_usage_question"
        active_counters = ToolUsageCounter.objects.filter(is_active=True, tool_id=usage_event.tool_id)
        active_counters = active_counters.filter(**{f"{counter_question_name}__isnull": False})
        for counter in active_counters:
            additional_value = 0
            counter_question_field = getattr(counter, counter_question_name)
            for question in self.questions:
                input_data = run_data_json[question.name] if question.name in run_data_json else None
                additional_value += get_counter_value_for_question(question, input_data, counter_question_field)
                if isinstance(question, PostUsageGroupQuestion):
                    for sub_question in question.sub_questions:
                        additional_value += get_counter_value_for_question(
                            sub_question, input_data, counter_question_field
                        )
            if additional_value:
                counter.value += counter.counter_direction * additional_value
                counter.save()

    def _report_problems(self, usage_event: UsageEvent, run_data_json: Dict, request):
        for question in self.questions:
            input_data = run_data_json[question.name] if question.name in run_data_json else None
            if isinstance(question, PostUsageRadioReportProblemQuestion):
                if "user_input" in input_data and input_data["user_input"] == "true":
                    from NEMO.views.tasks import save_task

                    task = Task(**question.options)
                    if task.force_shutdown is None:
                        task.force_shutdown = False
                    if task.safety_hazard is None:
                        task.safety_hazard = False
                    task.creator = usage_event.operator
                    task.tool = usage_event.tool
                    if task.urgency is None:
                        task.urgency = (
                            Task.Urgency.HIGH if task.safety_hazard or task.force_shutdown else Task.Urgency.NORMAL
                        )
                    save_task(request, task, usage_event.operator)
                    message = f"A problem report was automatically send to staff{' and the tool was shutdown' if task.force_shutdown else ''}"
                    messages.success(request, message, extra_tags="data-speed=9000")


def get_submitted_user_inputs(user_data: Union[str, dict]) -> Dict:
    """Takes the user data as a string or dict and returns a dictionary of inputs or a list of inputs for group fields"""
    user_input = {}
    try:
        user_data_json = loads(user_data) if isinstance(user_data, str) and user_data else user_data
        if user_data_json:
            for field_name, data in user_data_json.items():
                if "user_input" in data:
                    if data["type"] != "group":
                        user_input[field_name] = data["user_input"]
                    else:
                        user_input[field_name] = list(data["user_input"].values())
    except Exception as e:
        dynamic_form_logger.exception(e)
    return user_input


def render_group_questions(request, item, field_name: str, group_name: str) -> str:
    question_index = request.GET["index"]
    virtual_inputs = bool(strtobool((request.GET["virtual_inputs"])))
    dynamic_field = getattr(item, field_name, None)
    if dynamic_field:
        for question in PostUsageQuestion.load_questions(loads(dynamic_field), question_index):
            if isinstance(question, PostUsageGroupQuestion) and question.group_name == group_name:
                return question.render_group_question(virtual_inputs, item, field_name)
    return ""


def render_grid_questions(questions, item, dynamic_field_name: str, virtual_inputs: bool):
    # only use the grid if we have "form_row" defined for at least one item
    use_grid = max([q.form_row for q in questions if q.form_row], default=0)
    result = ""
    for row in sort_question_for_grid(questions):
        if row:
            extra_class = ""
            max_cells = len([q for q in row if (not isinstance(q, PostUsageFormulaQuestion) or q.show_formula_preview)])
            if use_grid and max_cells:
                cell_width = 12 // max_cells
                result += '<div class="row">'
                extra_class = f"col-md-{cell_width or 12}"
            for question in row:
                result += question.render(virtual_inputs, item, dynamic_field_name, extra_class)
            if use_grid and max_cells:
                result += "</div>"
    return result


def validate_consumable_for_question(question: PostUsageQuestion):
    if question.has_consumable:
        if not isinstance(question, (PostUsageNumberFieldQuestion, PostUsageFormulaQuestion)):
            raise Exception("Consumable withdrawals can only be used in questions of type number or formula")
        else:
            if question.consumable and question.consumable_id:
                raise Exception("Use consumable or consumable_id but not both")
            try:
                (
                    Consumable.objects.get(pk=question.consumable_id)
                    if question.consumable_id
                    else Consumable.objects.get(name=question.consumable)
                )
            except Consumable.DoesNotExist:
                match = f"id '{question.consumable_id}'" if question.consumable_id else f"name '{question.consumable}'"
                raise Exception(f"Consumable with {match} could not be found. Make sure the name/id matches.")


def withdraw_consumable_for_question(question, input_data, customer, merchant, project, usage_event, request):
    if isinstance(question, (PostUsageNumberFieldQuestion, PostUsageFormulaQuestion)):
        if question.has_consumable:
            consumable: Consumable = question.get_consumable()
            quantity = 0
            if input_data and "user_input" in input_data and input_data["user_input"]:
                if isinstance(input_data["user_input"], dict):
                    for user_input in input_data["user_input"].values():
                        if question.name in user_input and user_input[question.name]:
                            quantity += int(user_input[question.name])
                else:
                    quantity = int(input_data["user_input"])
            if quantity > 0:
                make_withdrawal(
                    consumable_id=consumable.id,
                    customer_id=customer.id,
                    merchant=merchant,
                    quantity=quantity,
                    project_id=project.id,
                    usage_event=usage_event,
                    request=request,
                )


def get_counter_value_for_question(question, input_data, counter_question):
    additional_value = 0
    if isinstance(question, (PostUsageNumberFieldQuestion, PostUsageFloatFieldQuestion)):
        if question.name == counter_question and "user_input" in input_data and input_data["user_input"]:
            if isinstance(input_data["user_input"], dict):
                for user_input in input_data["user_input"].values():
                    if question.name in user_input and user_input[question.name]:
                        additional_value += float(user_input[question.name])
            else:
                additional_value = float(input_data["user_input"])
    return additional_value


def validate_dynamic_form_model(dynamic_form_json: str, item, dynamic_field_name: str) -> List[str]:
    errors = []
    if dynamic_form_json:
        try:
            loads(dynamic_form_json)
        except ValueError:
            errors.append("This field needs to be a valid JSON string")
        try:
            dynamic_form = DynamicForm(dynamic_form_json)
            dynamic_form.validate(item, dynamic_field_name)
        except KeyError as e:
            errors.append(f"{e} property is required")
        except:
            error_info = sys.exc_info()
            errors.append(error_info[0].__name__ + ": " + str(error_info[1]))
    return errors


def admin_render_dynamic_form_preview(item, dynamic_field_name: str):
    form_validity_div = ""
    rendered_form = ""
    try:
        dynamic_form_json = getattr(item, dynamic_field_name, None)
        rendered_form = DynamicForm(dynamic_form_json).render(item, dynamic_field_name)
        if dynamic_form_json:
            form_validity_div = '<div class="form_validity"></div>'
    except:
        pass
    return mark_safe(
        '<div class="dynamic_form_preview">{}{}</div><div class="help dynamic_form_preview_help">Save form to preview</div>'.format(
            rendered_form, form_validity_div
        )
    )


def sort_question_for_grid(questions: List[PostUsageQuestion]) -> List[List[PostUsageQuestion]]:
    rows: List[List[PostUsageQuestion]] = []

    # Sorting the list of questions by row, None last
    row_cells = sorted(questions, key=lambda x: (x.form_row is None, x.form_row))

    # Extracting the unique rows
    unique_rows = sorted(set(q.form_row for q in row_cells if q.form_row is not None))
    # Adding row None at the end
    unique_rows.append(None)

    for row in unique_rows:
        # Extracting cells for the current row and sorting them
        cells_in_row = sorted(
            [q for q in row_cells if q.form_row == row], key=lambda x: (x.row_cell is None, x.row_cell)
        )
        rows.append(cells_in_row)

    return rows


def match_group_index(form_name: str) -> Optional[re.Pattern]:
    # This will match form_name or any combination of form_name_1, form_name_2 etc.
    return re.compile("^" + form_name + "(_(\d+))?$")


def get_js_event_data(item, dynamic_field_name: str, extra_data=None) -> str:
    if extra_data is None:
        extra_data = {}
    return dumps(
        {
            "item_type_id": ContentType.objects.get_for_model(item).id,
            "item_id": item.id,
            "field_name": dynamic_field_name,
            **extra_data,
        }
    )


def find_input_value_for_field(user_data: Union[str, dict], question_name) -> Optional[str]:
    try:
        user_data_json: dict = loads(user_data) if isinstance(user_data, str) and user_data else user_data
        if user_data_json:
            for field_name, data in user_data_json.items():
                if "user_input" in data:
                    if data["type"] != "group":
                        if question_name == field_name:
                            return data["user_input"]
                    else:
                        for group_index, group_data in data["user_input"].items():
                            for group_field_name, group_field_data in group_data.items():
                                name_with_index = f"{group_field_name}_{group_index}"
                                if (
                                    question_name == name_with_index
                                    or group_index == "0"
                                    and question_name == group_field_name
                                ):
                                    return group_field_data
    except Exception as e:
        dynamic_form_logger.exception(e)
    return ""


@require_GET
@login_required
def group_question(request, content_type_id, item_id, field_name, group_name):
    try:
        item = ContentType.objects.get(pk=content_type_id).get_object_for_this_type(pk=item_id)
        return HttpResponse(render_group_questions(request, item, field_name, group_name))
    except:
        dynamic_form_logger.exception("Error loading group question")
    return HttpResponse()


@require_POST
@login_required
def formula_preview(request, content_type_id, item_id, field_name, formula_name):
    try:
        item = ContentType.objects.get(pk=content_type_id).get_object_for_this_type(pk=item_id)
        try:
            data = loads(DynamicForm(getattr(item, field_name)).extract(request))
        except RequiredUnansweredQuestionsException as e:
            data = loads(e.run_data)
        input_data = find_input_value_for_field(data, formula_name)
        return HttpResponse(input_data if input_data is not None else "")
    except:
        dynamic_form_logger.exception("Error getting formula preview")
    return HttpResponse()


question_types: Dict[str, Type[PostUsageQuestion]] = {
    "number": PostUsageNumberFieldQuestion,
    "float": PostUsageFloatFieldQuestion,
    "textbox": PostUsageTextFieldQuestion,
    "textarea": PostUsageTextAreaFieldQuestion,
    "radio": PostUsageRadioQuestion,
    "radio_report_problem": PostUsageRadioReportProblemQuestion,
    "checkbox": PostUsageCheckboxQuestion,
    "dropdown": PostUsageDropdownQuestion,
    "formula": PostUsageFormulaQuestion,
    "group": PostUsageGroupQuestion,
}
