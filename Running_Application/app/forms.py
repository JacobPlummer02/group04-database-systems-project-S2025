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
    
class TrainingLogForm(forms.Form):
    date = forms.DateField(
        label='Date',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    workout_type = forms.CharField(
        label='Workout Type',
        max_length=50
    )
    duration = forms.CharField(
        label='Duration (HH:MM:SS)',
        max_length=8
    )
    distance_miles = forms.DecimalField(
        label='Distance (miles)',
        min_value=0,
        max_value=999.99,
    )

class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput)
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        if new_password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data