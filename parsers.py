import re

def nyaa_rss(tree):
	for item in tree.findall('.//item'):
		try:
			title, category, torrent_link, details_link, meta_string, date = (child.text for child in item.getchildren())
		except ValueError:
			continue
		print(title)
		#result = re.match('^([0-9]+) seeder\(s\), ([0-9]+) leecher\(s\), ([0-9]+) download\(s\)', meta_string)
		#result = result.groups()
		#if len(result) == 3:
		#	seeders, leechers, downloads = result
		#	print(downloads)