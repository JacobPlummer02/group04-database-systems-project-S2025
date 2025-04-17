from django import forms
import re

class RaceResultForm(forms.Form):
    event_id = forms.ChoiceField(label='Event')
    weather_id = forms.ChoiceField(label='Weather')
    result = forms.CharField(
        label='Result Time (MM:SS.DD)',
        max_length=10,
    )
    place = forms.IntegerField(label='Place')

    def format_result(self):
        result = self.cleaned_data['result']
        pattern = r'^\d{1,2}:\d{2}\.\d{2}$'
        if not re.match(pattern, result):
            raise forms.ValidationError("Enter result as MM:SS.DD")
        return result