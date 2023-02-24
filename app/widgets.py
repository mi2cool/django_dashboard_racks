from django.forms import DateTimeInput, TimeInput


class XDSoftDateTimePickerInput(DateTimeInput):
    template_name = 'widgets/xdsoft_datetimepicker.html'


class TimePickerInput(TimeInput):
    input_type = 'time'
