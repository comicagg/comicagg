"""Forms used in the API views."""
import logging
from django import forms

logger = logging.getLogger(__name__)

def vote_validator(value):
    """A vote is only valid if it's -1 <= vote <= 1."""
    logger.debug("Vote validator: " + str(value))
    if value < -1 or value > 1:
        raise forms.ValidationError("Vote value not valid")

class VoteForm(forms.Form):
    """Form used to validate the input of the vote for a comic."""
    vote = forms.IntegerField(validators=[vote_validator])

class StripForm(forms.Form):
	"""Form used to validate the input of the parameter"""
	strip_id = forms.IntegerField()

class SubscriptionForm(forms.Form):
	"""Form used to validate the input of the parameter"""
	# TODO: do we want to validate here?
	subscribe = forms.CharField()
