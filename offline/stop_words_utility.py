import csv

def get_words():
	reader = csv.reader(open("stop_words.csv", "rb"))
	for row in reader:
		return row

def store_words(words):
	writer = csv.writer(open("stop_words.csv", "wb"))
	writer.writerow(words)

def add_word(word):
	words = get_words()
	if word not in words:
		words.append(word)
		words.sort()
		store_words(words)	