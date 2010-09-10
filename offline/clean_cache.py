import os
import config
assert config.WEB_CACHE_DIR, 'You need to specify a valid web cache directory!'

def clean_cache_dir():
	for filename in os.listdir(config.WEB_CACHE_DIR):
		os.remove(os.path.join(config.WEB_CACHE_DIR, filename))
		print 'removed', filename
		
if __name__ == '__main__':
	clean_cache_dir()
	print 'DONE!'
