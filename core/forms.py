from django import forms

class CreateGameForm(forms.Form):
    host_name = forms.CharField(max_length=100, label="Your Name")
    imposters = forms.IntegerField(min_value=1, label="Number of Imposters")
    villagers = forms.IntegerField(min_value=1, label="Number of Villagers")
    healers = forms.IntegerField(min_value=0, label="Number of Healers")
    policemen = forms.IntegerField(min_value=0, label="Number of Policemen")