from django import template
register = template.Library()

@register.filter
def index(indexable, i):
	try:
		indexable[i]
		n = i
	except:
		n = 0
	
	return indexable[n]