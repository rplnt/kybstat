base_url = ''
username = ''
password = ''
template = ''
sqlitedb = ''
waittime = 0.9
first_id = ''
final_id = ''
t_format = '%Y-%m-%d %H:%M:%S'
dumpnode = ''
add_time = 1

try:
	from private_settings import *
except ImportError:
	pass