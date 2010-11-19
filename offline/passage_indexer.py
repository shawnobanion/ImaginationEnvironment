import sys
import lucene_indexer
import simplejson

filenames = {'Buddhism': 'buddha.json', 'Christianity': 'bible.json', 'Hinduism': 'vedas.json', 'Islam': 'quran.json'}
INDEX_ROOT_DIR = 'index'
MAX_LINES_PER_PASSAGE = 9
MAX_CHARS_PER_LINE = 25

def load_passages(filename, max_chapters=sys.maxint):
    text = simplejson.load(open(filename, 'r'))
    passages = []
    chapter_count = 0

    for chapter in text:
        lines = []
        curr_line = []
        char_count = 0
        total_verses = len(chapter['verses'])
        
        for verse_num, verse in enumerate(chapter['verses']):
            for word in verse.split():
                if char_count + 1 + len(word) < MAX_CHARS_PER_LINE:
                    curr_line.append(word)
                    char_count += len(word)
                else:
                    lines.append(' '.join(curr_line))
                    if len(lines) == MAX_LINES_PER_PASSAGE:
                        passages.append(create_index_obj(' ||| '.join(lines), filename))
                        lines = []
                    curr_line = [word]
                    char_count = 0
        
        if any(curr_line):
            lines.append(' | '.join(curr_line))
        
        if any(lines):
            passages.append(create_index_obj(' '.join(lines), filename))
        
        chapter_count += 1
        if chapter_count >= max_chapters:
            return passages
    
    return passages

def create_index_obj(text, religion):
	return { 'contents' : text, 'religion' : religion }

def add_passages(passages):
	lucene_indexer.IndexObjects(passages, INDEX_ROOT_DIR)

if __name__ == '__main__':
	passages = []
	passages.extend(load_passages(filenames['Islam']))
	passages.extend(load_passages(filenames['Hinduism']))
	add_passages(passages)