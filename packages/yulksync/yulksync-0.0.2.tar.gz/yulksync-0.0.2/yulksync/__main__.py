# 2025.10.18   python -m yulksync en/cn/all
import requests,os,fire # fire>=0.7.1  wget>=3.2  | pip install pywin32
import win32com.client
from pathlib import Path
host	= 'file.yulk.net'
root	= os.path.dirname(os.path.abspath(__file__)).replace('yulksync','yulk') 

def create_desktop_shortcut(
    target_path,
    shortcut_name=None,   # not contains .lnk
    description="",
    working_directory="",
    icon_path="",
    arguments=""   # start args
):
	desktop_path = Path.home() / "Desktop"
	if shortcut_name is None:
		shortcut_name = Path(target_path).stem
	shortcut_path = desktop_path / f"{shortcut_name}.lnk"

	shell = win32com.client.Dispatch("WScript.Shell")
	shortcut = shell.CreateShortCut(str(shortcut_path))
	shortcut.TargetPath = str(target_path)
	shortcut.Description = description
	shortcut.Arguments = arguments

	if working_directory:
		shortcut.WorkingDirectory = str(working_directory)
	else:
		shortcut.WorkingDirectory = str(Path(target_path).parent)

	if icon_path:
		shortcut.IconLocation = str(icon_path)

	shortcut.Save()
	return shortcut_path

def download_with_wget(url, local_filename):
	import wget
	try:
		if os.path.exists(local_filename):
			os.remove(local_filename)
		print ("Start to download: ",  url , flush=True) 
		wget.download(url, local_filename)
		print(f"\nDone: {local_filename}")
	except Exception as e:
		print(f"\nFailed: {e}", url, local_filename)

def run(name): 
	''' python -m yulksync en/cn/all/par/park/parkv/parx/myu/ce | python -m yulksync par/myusnt.parquet '''
	if name =='hello':
		create_desktop_shortcut("marimo", arguments="run http://file.yulk.net/mo/hello.py")
	elif name == 'edit':
		create_desktop_shortcut("marimo", shortcut_name='SQLPY', working_directory=f"{root}/mo", arguments="edit")
	elif name == 'sql9855':
		create_desktop_shortcut("start9855.bat", shortcut_name='Sql9855', working_directory=f"{root}")
	elif name == 'mklink':
		#os.system(f'runas /user:Administrator "mklink /D \"/yulk\" {root}" ')
		os.system(f'mklink /J "/yulk" {root}') # /yulk/parx
	elif name == 'logo':  
		mo_root = root.replace('yulk', 'marimo')
		download_with_wget(f"http://{host}/static/logo.png", f"{mo_root}/_static/logo.png")
	elif name.endswith('.parquet'):  # python -m yulksync par/ce.parquet
		download_with_wget(f"http://{host}/{name}", f"{root}/{name}")
	else:
		for line in requests.get(f"http://{host}/yulksync/{name}.txt").text.strip().split('\n'):  # par/myu.parquet
			try:
				line = line.strip()
				if not line: continue 
				print (line, flush=True)
				download_with_wget(f"http://{host}/{line}", f"{root}/{line}")
			except Exception as e:
				print(f"\nFailed: {e}", line, root)

if __name__ == "__main__": 	#print( create_desktop_shortcut("marimo", arguments="edit") )
	fire.Fire(run)

'''
# 使用示例
if __name__ == "__main__":
    # 示例1：创建记事本快捷方式
    create_desktop_shortcut(
        target_path=r"C:\Windows\System32\notepad.exe",
        shortcut_name="我的记事本",
        description="快速打开文本编辑器",
        icon_path=r"C:\Windows\System32\notepad.exe,0"
    )
    
    # 示例2：创建带参数的快捷方式
    create_desktop_shortcut(
        target_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        shortcut_name="Google Chrome - 无痕模式",
        arguments="--incognito",
        description="以无痕模式打开Chrome浏览器"
    )
'''