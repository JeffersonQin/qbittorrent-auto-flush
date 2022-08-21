import sys
import os
import time
import yaml
import traceback
from ftplib import FTP, error_perm


def uploadFile(ftp, name, localpath):
	"""upload single file"""
	print("STOR", name, localpath)
	ftp.storbinary('STOR ' + name, open(localpath,'rb'))


def makeDir(ftp, name):
	"""Make directory, ignore if exists"""
	print("MKD", name)
	try:
		ftp.mkd(name)
	# ignore "directory already exists"
	except error_perm as e:
		if not e.args[0].startswith('550'): 
			raise


def placeFiles(ftp, path):
	"""place files under this path to the current path on server through FTP"""
	for name in os.listdir(path):
		localpath = os.path.join(path, name)
		if os.path.isfile(localpath):
			uploadFile(ftp, name, localpath)
		elif os.path.isdir(localpath):
			makeDir(ftp, name)
			print("CWD", name)
			ftp.cwd(name)
			placeFiles(ftp, localpath)           
			print("CWD", "..")
			ftp.cwd("..")


if __name__ == '__main__':
	root_dir = os.path.split(os.path.abspath(__file__))[0]
	config_dir = os.path.join(root_dir, 'config.yml')
	log_dir = os.path.join(root_dir, 'logs')
	timestr = time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time()))
	logfile_dir = os.path.join(log_dir, f'{timestr}.txt')

	os.makedirs(log_dir, exist_ok=True)
	sys.stdout = open(logfile_dir, 'w+')

	args = sys.argv
	category = args[1]
	path = ' '.join(args[2:])

	try:
		print('Category: {}'.format(category))
		print('Path: {}'.format(path))
		with open(config_dir, 'r', encoding='utf8') as f:
			contents = f.read()
			config = yaml.load(contents, Loader=yaml.FullLoader)
		target_dir = os.path.join(config['target-dir'], category)
		print('Target dir: {}'.format(target_dir))

		from ftplib import FTP
		ftp = FTP()
		ftp.set_debuglevel(2)
		ftp.connect("192.168.31.215", 21)
		ftp.login(config['username'], config['password'])
		ftp.cwd(config['target-dir'])
		makeDir(ftp, category)
		ftp.cwd(category)

		if os.path.isdir(path):
			makeDir(ftp, os.path.basename(path))
			ftp.cwd(os.path.basename(path))
			placeFiles(ftp, path)
		else:
			uploadFile(ftp, os.path.basename(path), path)
		print('Copied to {}'.format(os.path.join(target_dir, os.path.basename(path))))
		print('SUCCESS')
	except Exception as e:
		print(e)
		traceback.print_exc()
		print('FAILED')
		print('PRESS ENTER TO CONTINUE ...')
		input()
