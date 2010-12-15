import BeautifulSoup

def read_tag_int(tag):
	return int(read_tag_utility(tag).strip())
	
def read_tag(tag):
	return read_tag_utility(tag).strip()

def read_tag_utility(tag):
	line = ''
	if not tag:
		return ''
	if tag.string:
		return ' ' + tag.string
	for i, text in enumerate(tag):
		line += read_tag(text)
	return line