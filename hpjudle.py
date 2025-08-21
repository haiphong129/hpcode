from app import app
from flask import Flask, render_template, redirect, url_for, request, session,flash, jsonify, Response
from flask_login import current_user, login_user, logout_user, login_required
from app.models import * #User, Yeucaugv, Post, Runexam, Contest, Contest_post, History,Submitcode
import os, subprocess, time, shutil
from threading import Timer
from hpfunction import *
from datetime import timedelta
app.app_context().push()
def createlog(flog,st,flag=None,tce=None):#ghi mới (flag=0) hoặc ghi vào cuối (flag=None) tệp hoặc đầu tệp (flag=1)
	#tce là id của testcacse
	for tmpxre in ["hpelearning","tmp","app","static","chambai","D:","C:","\\\\"]:
		st=st.replace(tmpxre,"")#.replace("[","")#str(random.randint(1,1000))
	if flag is None:
		f=open(flog,'a',encoding='utf-8')
	elif flag==1:#ghi vào đầu tệp
		f=open(flog,'r',encoding='utf-8')
		datatmp  = f.readline()
		datatmp  = f.read()
		f.close()
		st = st + "\n" +datatmp
		f=open(flog,'w',encoding='utf-8')
	elif flag==0: #ghi mới
		f=open(flog,'w',encoding='utf-8')
	f.write(st)
	if tce is not None:
		#onclick="window.open('http://www.website.com/page')"
		st = " <a target='_blank' href=\'"+""+"../gettests/?id="+str(tce)+"\'>Xem test</a>"
									 
		
		f.write(st)
	if "Result" not in st: f.write("\n")
	f.close()
	#shutil.copy(flog,"app/static/chambai/tmp/"+user.username+".log")
	f=open(flog,'r',encoding='utf-8')
	datatmp  = f.read()
	f.close()
	idlog = flog.split("/")[-1].split('.')[0]
	if "check_hack" in idlog: return 
	idlog=int(idlog)
	sb = Submitcode.query.filter_by(id=idlog).first()
	if sb is None: return
	sb.log = datatmp
	db.session.commit()
def c1(st): #Xử lý cho trình chấm C1: So sánh hai từ giống nhau theo đúng thứ tự xuất hiện. Có hai dấu cách liên tiếp,
			#hoặc có dòng trống ở đầu, cuối không ảnh hưởng đến kết quả
	char=['\r\n','\n','\t','  ']
	for c in char: st=st.replace(c,' ')
	while '  ' in st: st=st.replace('  ',' ')
	if len(st)>0 and st[0] ==' ': st=st[1:]
	if len(st)>0 and st[-1]==' ': st=st[:-1]
	return st

def trinhcham_c1(out,ans): #Không phân biệt HOA/thường
	out=c1(out).lower()
	ans=c1(ans).lower()
	#print(out+'.',ans+'.')
	if out==ans: return 1,"<span class='text-success'>Kết quả <b>đúng</b></span>. "
	return 0,"<span class='text-danger'>Kết quả <b>sai</b></span>. "

def trinhcham_c2(out,ans): #Như trình chấm C1 nhưng PHÂN BIỆT HOA/thường
	out=c1(out)
	ans=c1(ans)
	if out==ans: return 1,"<span class='text-success'>Kết quả <b>đúng</b></span>. "
	return 0,"<span class='text-danger'>Kết quả <b>sai</b></span>. "
def trinhcham_c3(out,ans,e=None):  # So khớp các từ theo đúng thứ tự, nếu hai từ là xâu thì phải giống nhau hoàn toàn
							  # Nếu hai từ là số thực thì có độ lệch nhỏ hơn e (mặc định 1e-5)
							  # Việc thừa các dòng đầu tiên, dòng cuối cùng và ký tự trắng không ảnh hưởng đến kết quả
	out=c1(out).split(' ')
	ans=c1(ans).split(' ')
	if e is None: e=0.00001
	e=float(e)
	truex=0
	for i in range(min(len(out),len(ans))):
		x=float(out[i]) if out[i].replace('.','',1).isdigit() else None
		y=float(ans[i]) if ans[i].replace('.','',1).isdigit() else None
		if (x and y and abs(x-y)<=e):  truex=truex+1
	if truex==max(len(out),len(ans)): return 1,"<span class='text-success'>Kết quả <b>đúng</b></span>. "
	if truex==0: return 0,"<span class='text-danger'>Kết quả <b>sai</b></span>. "
	return truex/max(len(out),len(ans)),"<span class='text-warning'>Đúng một phần</span>. "
def trinhcham_s1(out,ans): #So sánh hai xâu giống nhau hoàn toàn, sự khác nhau cho dù một ký tự trắng hoặc ký tự
							# xuống dòng vẫn xem là khác nhau (trừ dấu xuống dòng cuối xâu)
	ans=ans.replace("\r\n"," ")
	out=out.replace("\r\n"," ")
	while(len(ans)>0 and ans[-1]==' '): ans=ans[:-1]
	while(len(out)>0 and out[-1]==' '): out=out[:-1]
	if out==ans: return 1,"<span class='text-success'>Kết quả <b>đúng</b></span>. "
	return 0,"<span class='text-danger'>Kết quả <b>sai</b></span>. "
def trinhcham_s2(out,ans): #Tương tự như trình chấm s1 nhưng KHÔNG phân biệt HOA/thường
	ans=ans.replace("\r\n"," ")
	out=out.replace("\r\n"," ")
	while(len(ans)>0 and ans[-1]==' '): ans=ans[:-1]
	while(len(out)>0 and out[-1]==' '): out=out[:-1]
	if out.lower()==ans.lower(): return 1,"<span class='text-success'>Kết quả <b>đúng</b></span>. "
	return 0,"<span class='text-danger'>Kết quả <b>sai</b></span>. "
def fwriteex(fn,data):
	fn='app/static/chambai/chamngoai/'+fn
	f=open(fn,"w")
	f.write(str(data))
	f.close()
def trinhcham_ex(d,outp,idx):
	idx = int(idx.split('.')[0].split('/')[-1])
	sb = Submitcode.query.filter_by(id=idx).first()
	if sb is None: return 0,"Không tìm tháy bản ghi"
	pr = Post.query.filter_by(id=sb.problem).first()
	if pr is None: return 0,"Không tìm thấy bài tập"
	fn=pr.id_p
	fn = 'app/static/chambai/chamngoai/'+fn+".py"
	if os.path.isfile(fn) == False: return 0,"Không tìm thấy trình chấm"
	
	fwriteex(pr.id_p+".inp",d['inp'].decode()) #input
	fwriteex(pr.id_p+".out",d['out'])		   #output
	fwriteex(pr.id_p+".ans",outp)			   #trả lời của người nộp bài
	p=subprocess.Popen(['python',fn],stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
	check, err=p.communicate()
	status = "<span class='text-warning'> Đúng 1 phần <b>sai</b></span>. "
	if float(check)==1: status = "<span class='text-success'>Kết quả <b>đúng</b></span>. "
	if float(check)==0: status = "<span class='text-danger'>Kết quả <b>sai</b></span>. "
	return float(check),status

def writeerror(idx,pollid):
	f=open("Error.txt","a",encoding="utf-8")
	f.write(str(pollid)+"\n"+str(idx)+"\n")
	f.close()
def chambai(fn,fn_exe,flog,tc,config,ext):
	numtrue=0
	timeout=config['exe'] if ext!='py' else config['py']
	if ext=='sb3': timeout = 5
	flagout=None
	flagerr={3221225477:"STATUS_ACCESS_VIOLATION",3221225620:"Division by zero",1:"Time Limit Exceeded"}
	if(len(tc)==1 and tc[0]["out"]==""): flagout=0
	for i,d in enumerate(tc):
		st= '----'+"test"+str(i)+': '
		start_time = time.time()
		if ext in ['pas','cpp']:
			start_time=time.time()
			p=subprocess.Popen(fn_exe,stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.STDOUT)
			timer = Timer(timeout+0.2, p.kill)
			err=None
			try:
				timer.start()
				if type(d['inp']) is str: outp, err=p.communicate(input=d['inp'].encode())
				else: outp, err=p.communicate(input=d['inp'])
			finally:
				finish_time=time.time()
				timer.cancel()
			#finish_time=time.time()
			#print("p.poll()",p.poll())
			timestr=" "+str(round(finish_time-start_time,3))
			stx=None #đánh dấu không gặp lỗi khi chấm bài
			if p.poll()==0 and finish_time-start_time>timeout: stx= "<span class='text-danger'>Time Limit Exceed. "+timestr+"(s)</span>"
			if p.poll()==1 and stx is None: stx="<span class='text-danger'>Time Limit Exceed. </span>"
			if p.poll()!=0 and stx is None: stx="<span class='text-danger'>Exit code: "+ str(p.poll()) +"</span>"
			if stx is not None:
				createlog(flog=flog,st=st+stx,flag=flagout,tce=d["id"])
				continue			
		elif ext=='py':
			start_time=time.time()
			p=subprocess.Popen([os.getcwd()+'/app/static/judle/PYTHON/python.exe',fn],stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
			timer = Timer(timeout+0.2, p.kill)
			try:
				timer.start()
				if type(d['inp']) is str: outp, err=p.communicate(input=d['inp'].encode())
				else: outp, err=p.communicate(input=d['inp'])
			finally:
				timer.cancel()
			finish_time=time.time()	
			timestr=str(round(finish_time-start_time,3))
			
			if "Error:" in err.decode():
				tmperr=err.decode().replace("\r\n","\n")#.replace("app/static/chambai","")
				tmperr=tmperr.replace("line","<span class='text-danger'>line</span>")+"<br> Testcase"+str(i)
				createlog(flog,tmperr,0,tce=d["id"])
				return 0
			stx=None
			if p.poll()==0 or p.poll()==1:
				if finish_time-start_time>=timeout:
					stx="<span class='text-danger'>Time Limit Exceed. "+timestr+"(s)</span>"
			if p.poll()==3221225620 and stx is None: stx = "<span class='text-danger'>Division by zero. </span>"
			if p.poll()!=0 and stx is None: stx = "<span class='text-danger'>Run Time Error. </span>"
			if stx is not None:
				createlog(flog,st+stx,flagout,tce=d["id"])
				writeerror(fn,p.poll())
				continue
		elif ext=='sb3':
			data, temp = os.pipe()
			os.write(temp, bytes(d['inp'], "utf-8"))
			os.close(temp)
			print(fn)
			start_time=time.time()
			outp = subprocess.check_output(os.getcwd()+"/app/static/judle/scratch-run.exe "+ fn, stdin=data, shell=True, timeout=timeout+0.2)
			finish_time=time.time()	
			timestr=str(round(finish_time-start_time,3))
			if finish_time-start_time>timeout:
				stx="<span class='text-danger'>Time Limit Exceed. "+timestr+"(s)</span>"
				createlog(flog,st+stx,flagout,tce=d["id"])
				continue
			#print(outp.decode("utf-8"))
		else:
			print(ext) 
			continue		
		try:
			outp=outp.decode().replace('\00',"")
		except:
			outp = ""
		if flagout==0:#Trường hợp chấm ví dụ
			print("flog",flog)
			outp = outp.replace(" ","&nbsp;")
			createlog(flog,outp+"\nTime: "+timestr+"(s)",0)
		else:
			if config['tc']=='c1': check,statust=trinhcham_c1(d['out'],outp)
			if config['tc']=='c2': check,statust=trinhcham_c2(d['out'],outp)
			if config['tc']=='c3': check,statust=trinhcham_c3(d['out'],outp,config['e'])
			if config['tc']=='s1': check,statust=trinhcham_s1(d['out'],outp)
			if config['tc']=='s2': check,statust=trinhcham_s2(d['out'],outp)
			if config['tc']=='ex': check,statust=trinhcham_ex(d,outp,fn) #trình chấm ngoài
			createlog(flog=flog,st=st+statust + " "+ timestr +'(s)',tce=d["id"])
			#cho phép xem testcase, user phải thuộc đối tượng xem test
			numtrue+=check
		
	if flagout!=0: createlog(flog,'Result: '+str(numtrue)+'/'+str(len(tc)),1) #ghi vào đầu tệp
	return numtrue

def jundle():
	try:
		f=open('app/static/chambai/checkpoint.txt','r')
		d=int(f.read())
		f.close()
		if d==1: return
		for i in range(5):
			time.sleep(0.1)
			tmp = Submitcode.query.filter_by(graded=0)
			for x in tmp.order_by(Submitcode.id.desc()).limit(10).all():
				fn="app/static/chambai/tmp/"+str(x.id)+"."+x.ext+".log"
			sc = Runexam.query.filter_by(graded=0).first()#.order_by(Runexam.id.desc())
			flag=0
			if sc is None:
				flag=1
				sc = Submitcode.query.filter_by(graded=0).first()
				if sc is None: sc = Submitcode.query.filter_by(graded=2).first() #Các bài chấm lại
			if sc is None : break #continue
			sc.graded=1
			db.session.commit()
			if sc.code is None: continue
			print("running",sc.id,flag,end="...")
			fn="app/static/chambai/tmp/"+str(sc.id)+"."+sc.ext
			fn_exe,flog=fn[:-3]+'exe',fn+".log"
			f=open(fn,"w",encoding="utf-8")
			f.write(sc.code.replace("\r\n","\n"))
			f.close()

			if flag==0: #Ví dụ
				post=Post.query.filter_by(id=sc.idp).first()
				tc=[{"inp":sc.inp.encode(),"out":"","id":None}]
			else:
				post=Post.query.filter_by(id=sc.problem).first()
				if post is None: 
					db.session.commit()
					continue				
				tc=[]
				prefix = post.id_p[0] if post.id_p[0] not in ['0','1','2','3','4','5','6','7','8','9'] else '0-9'
				fntest= app.config['TESTCASE']+prefix+"/"+post.id_p
				for t in post.testcase.all():
					inp,out=get1test(fntest,t.fnstt)
					tc.append({"inp":inp,"out":out,"id":t.id})
				if len(tc)==0:
					db.session.commit()
					continue

			#Lấy cài đặt chấm bài của bài tập
			config={'exe':2,'py':2,'point':50,'tc':'c1','e':0.00001,'memory':1024}
			cf=Config.query.filter_by(idp=post.id).first()
			numtrue=0
			if cf is not None:
				config={'exe':cf.tlexe,'py':cf.tlpy,'point':50,'tc':cf.juger,'e':cf.exp,'memory':cf.memory}
			user=User.query.filter_by(username=sc.user).first()
			
			if sc.ext in ['cpp','pas']:
				createlog(flog,'Đang dịch...',0)
				
				if sc.ext=='cpp': x = subprocess.getoutput(os.getcwd()+'/app/static/judle/CodeBlocks/MinGW/bin/g++.exe -std=c++1y ' + fn + ' -o ' + fn_exe+' -Wl,--stack,66060288')#+' -Wl,--stack,66060288'
				if sc.ext=='pas': x = subprocess.getoutput(os.getcwd()+'/app/static/judle/FPC/bin/i386-win32/fpc.exe ' + fn)
				if x=="" or 'error' not in x.lower():#Dịch thành công
					createlog(flog,x+'\nDịch thành công. Đang chấm...',0)
					numtrue = chambai(fn,fn_exe,flog,tc,config,sc.ext)
				else:
					x=x.replace("error","<span class='text-danger'>error</span>") 
					createlog(flog,x.replace("app/static/chambai/tmp/",""))
			if sc.ext == 'py':
				createlog(flog,'Đang chấm...',0)
				numtrue = chambai(fn,fn_exe,flog,tc,config,sc.ext)
			if sc.ext =='sb3':
				createlog(flog,'Đang chấm...',0)
				fn= "C:/Alltest/Scratch/"+sc.code
				numtrue = chambai(fn,fn_exe,flog,tc,config,sc.ext)

			createlog(flog,'======xong======')
			print("xong")
			
			if flag==1:
				f=open(flog,"r",encoding="utf-8")
				sc.log=f.read()
				f.close()
				sc.numtest=numtrue
				post=Post.query.filter_by(id=sc.problem).first()
				sbtmp=Submitcode.query.filter(Submitcode.ext=='sb3',Submitcode.user==user.username,Submitcode.problem==post.id,Submitcode.fulltest==1)
				sball=Submitcode.query.filter(Submitcode.ext=='sb3',Submitcode.problem==post.id,Submitcode.fulltest==1)
				countAC=Submitcode.query.filter(Submitcode.user!='admin',Submitcode.problem==post.id,Submitcode.fulltest==1).count()
				print(numtrue,len(tc))
				if numtrue==len(tc): 
					sc.fulltest=1
					if sbtmp.count()==1 and sc.ext == 'sb3': 
						user.ndow+=20
						user.thoihan += timedelta(days=5)
					if sball.count()==1 and sc.ext == 'sb3': user.ndow+=80
					if countAC==0: countAC+=1
					user.ndow+=round(12/countAC,2)
					user.thoihan += timedelta(days=round(5/countAC,2))

					db.session.commit()
				db.session.commit()
				updaterankonequery(sc,user,post)
		
		f=open('app/static/chambai/checkpoint.txt','w')
		f.write("0")
		f.close()
		print("Dừng chương trình chấm")
	except Exception as e:
		f=open("Error.txt","a",encoding="utf-8")
		f.write("\n\n"+str(e)+"\n\n")
		f.close()
		print(str(e))
	return