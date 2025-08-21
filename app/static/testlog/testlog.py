import os, subprocess, time, psutil, datetime
import sqlite3
from zipfile import ZipFile
import pathlib
import concurrent.futures as futures
import sys
import tempfile
class Logger():
    stdout = sys.stdout
    messages = []

    def start(self): 
        sys.stdout = self

    def stop(self): 
        sys.stdout = self.stdout

    def write(self, text): 
        self.messages.append(text)
log = Logger()

def timeout(timelimit):
    def decorator(func):
        def decorated(*args, **kwargs):
            with futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    result = future.result(timelimit)
                except futures.TimeoutError:
                    print('Timedout!')
                    #raise TimeoutError from None
                    
                # else:
                #     print(result)
                
                executor._threads.clear()
                
                futures.thread._threads_queues.clear()
                
                return result
        return decorated
    return decorator
@timeout(5)
def calll(p,timeout,inp):
	outp, err = p.communicate(timeout=timeout,input=inp)
	return outp,err

def chamcpp_pas(fn_exe,fn_in,config):
	f=open(fn_in,"rb")
	inp=f.read()
	f.close()
	outp=""
	try:
		p=subprocess.Popen([fn_exe],stdout=subprocess.PIPE,stdin=subprocess.PIPE)
		outp, err = calll(p,config['exe'],inp)#p.communicate(timeout=config['exe'],input=inp)
		outp=outp.decode('utf-8')
	except Exception as e: 	outp=str(e)
	f=open(fn_in.replace('inp','out'),"w",encoding="utf-8")
	f.write('.'+outp)
	f.close()
def deleteinp_out():
	folder='logs/'
	for fn in os.listdir(folder):
		fname = pathlib.Path(folder+fn)
		subtime=datetime.datetime.now()-datetime.datetime.fromtimestamp(fname.stat().st_mtime)
		second=subtime.total_seconds()
		if second<=10*60: continue
		try:
			os.remove(folder+fn)
			print(folder+fn)
		except:
			print('cant delete file',folder+fn)
def runtet():
	deleteinp_out()
	config={'exe':2,'py':2,'point':50,'tc':'c1','e':0.00001,'memory':1024}
	files=os.listdir('upload/')
	time.sleep(0.2)#Dừng x(s)
	# while (len(files)>0) and ( files[0].split('.')[-1].lower() not in ['cpp','pas','py']): files=files[1:]
	# if len(files)==0: return
	fn=""
	while 1:
		files=os.listdir('upload/')
		if len(files)==0: return
		fn=files[0]
		if fn.split('.')[-1].lower() not in ['cpp','pas','py']:
			try:
				os.remove(os.path.join("upload",fn))
			except:
				print("Can't delete ",os.path.join("upload",fn))
			return
		fn=os.path.join('upload',fn)
		break
	if fn=="":return
	fn_exe=fn[:-3]+'exe'
	fn_inp=os.path.join('logs',files[0].split('.')[0]+".inp")
	ext=fn.split('.')[-1]
	print(fn)
	if(ext in ['cpp','pas']):
		print('-------- Đang dịch...',end="")
		if ext=='cpp': x = subprocess.getoutput('g++ -std=c++1y ' + fn + ' -o ' + fn_exe)
		if ext=='pas': x = subprocess.getoutput('fpc ' + fn)
		print('Done...')
		if x=="" or 'compiled' in x:#Dịch thành công
			print("-------- Đang chấm...",end="")
			chamcpp_pas(fn_exe,fn_inp,config)
		else:
			f=open(fn_inp.replace('inp','out'),"w",encoding="utf-8")
			f.write('.'+x.replace("upload","").replace("\n","<br>"))
			f.close()
	if ext=='py':
		print("--------Đang chấm....")
		f=open(fn_inp,"rb")
		inp=f.read()
		f.close()
		outp=""
		print(inp)
		x=subprocess.Popen(['python',fn],stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
		try:
			outp, err = x.communicate(timeout=config['py'],input=inp)
			outp='.'+outp.decode('utf-8')
			outp=outp+err.decode('utf-8')
		except Exception as e:
			outp="."+str(e)
			x.kill()
		f=open(fn_inp.replace('inp','out'),"w",encoding="utf-8")
		f.write(outp)
		f.close()
	try:
		os.remove(fn)
		for p in psutil.process_iter():
			if '[exam]' in p.name(): p.kill()
	except:
		print('can not delete file',fn)
	print('Done...')
if __name__ == "__main__":
	while 1: 
		try:
			runtet()
		except Exception as e: 
			print(e)
