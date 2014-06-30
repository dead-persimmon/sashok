def local_run():
	from os.path import isfile as is_file
	return is_file('local.debug')